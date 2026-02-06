import smartpy as sp

@sp.module
def main():

    poke_ticket: type = sp.ticket[sp.address]
    feedback_function: type = sp.lambda_[sp.address, sp.string]

    def default_feedback(source_address: sp.address):
        return "Hello!"

    def new_feedback(source_address: sp.address):
        return "You poked me!"

    class PokeContract(sp.Contract):
        def __init__(self, admin: sp.address):
            sp.cast(self.data.messages, sp.map[sp.address, sp.string])
            self.data.messages = {}
            sp.cast(self.data.tickets, sp.map[sp.address, poke_ticket])
            self.data.tickets = {}
            self.data.admin = admin

            self.data.feedback_function = default_feedback
            sp.cast(self.data.feedback_function, feedback_function)

        @sp.entrypoint
        # Admin only: create a poke ticket for a given address
        def create_ticket(self, user_address: sp.address):
            with sp.modify_record(self.data) as data:
              if sp.source != data.admin:
                  raise "Only admin can create tickets"
              # To avoid overwriting and destroying an existing ticket, verify that the user does not have a ticket
              (ticket_opt, ticket_map_without_user) = sp.get_and_update(user_address, None, data.tickets)
              match ticket_opt:
                  case Some(ticket):
                      raise "User already has a ticket"
                  case None:
                      new_ticket = sp.ticket(user_address, sp.nat(1))
                      new_ticket_map = sp.update_map(user_address, sp.Some(new_ticket), ticket_map_without_user)
                      data.tickets = new_ticket_map

        @sp.entrypoint
        def update_feedback(self, new_function: feedback_function):
            with sp.modify_record(self.data) as data:
                if sp.source != data.admin:
                    raise "Only admin can create tickets"
                data.feedback_function = new_function

        @sp.entrypoint
        def poke(self):
            # No message was sent, so use an empty string
            with sp.modify_record(self.data) as data:
                new_messages = sp.update_map(sp.sender, sp.Some(""), data.messages)
                data.messages = new_messages

        @sp.entrypoint
        def poke_with_message(self, message: sp.string):
            # Include received message in storage
            with sp.modify_record(self.data) as data:
                new_messages = sp.update_map(sp.sender, sp.Some(message), data.messages)
                data.messages = new_messages

        @sp.entrypoint
        def poke_other_contract(self, target_address: sp.address):
            with sp.modify_record(self.data) as data:
              # Check that the user has a ticket
              (ticket_opt, updated_tickets) = sp.get_and_update(sp.source, None, data.tickets)
              user_ticket = ticket_opt.unwrap_some(error="User needs a ticket to poke another contract")

              # Update the tickets in storage
              data.tickets = updated_tickets

              # Get the contract
              contract_opt = sp.contract(poke_ticket, target_address, entrypoint="poke_me_back")
              # contract = contract_opt.unwrap_some("Failed to find contract")
              # sp.transfer(user_ticket, sp.mutez(0), contract)
              # Call the contract and pass the ticket
              match contract_opt:
                  case None:
                      raise "Failed to find contract"
                  case Some(contract):
                      sp.transfer(user_ticket, sp.mutez(0), contract)


        # Receive a request from another contract and poke them back
        # Destroys the passed ticket
        @sp.entrypoint
        def poke_me_back(self, passed_ticket: poke_ticket):
            with sp.modify_record(self.data) as data:

              # Verify that the sender and ticket have the same address
              # This destroys the passed_ticket variable if it succeeds
              (ticket_data, _new_ticket) = sp.read_ticket(passed_ticket)
              if sp.sender != ticket_data.ticketer:
                  raise "Sender does not match ticket address"

              # Call the same contract back
              contract_opt = sp.contract(sp.string, sp.sender, entrypoint="poke_with_message")
              match contract_opt:
                  case Some(contract):
                      sp.transfer(data.feedback_function(sp.sender), sp.mutez(0), contract)
                  case None:
                      sp.trace("Failed to find contract")


@sp.add_test()
def test():
    scenario = sp.test_scenario("poke_contract")
    admin = sp.test_account("Admin")
    contract = main.PokeContract(admin.address)
    scenario += contract

    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")

    contract.poke(_sender=alice)
    contract.poke(_sender=bob)

    scenario.verify(contract.data.messages.get(alice.address) == "")
    scenario.verify(contract.data.messages.get(bob.address) == "")

    contract.poke_with_message("Hello", _sender=alice)
    scenario.verify(contract.data.messages.get(alice.address) == "Hello")

    contract2 = main.PokeContract(admin=admin.address)
    scenario += contract2

    # Can't poke another contract without a ticket
    contract.poke_other_contract(contract2.address, _sender=alice.address, _valid=False)
    # Create a ticket and poke contract 2 via contract 1
    contract.create_ticket(alice.address, _sender=admin.address)
    contract.poke_other_contract(contract2.address, _sender=alice.address)
    scenario.verify(contract.data.messages.get(contract2.address) == "Hello!")

    # Change the feedback function
    contract2.update_feedback(main.new_feedback, _source=admin.address)
    # Create a ticket and poke contract 2 via contract 1 again
    contract.create_ticket(alice.address, _sender=admin.address)
    contract.poke_other_contract(contract2.address, _sender=alice.address)
    scenario.verify(contract.data.messages.get(contract2.address) == "You poked me!")
