import smartpy as sp

@sp.module
def main():
    class PokeContract(sp.Contract):
        def __init__(self, initial_message: sp.string):
            sp.cast(self.data.messages, sp.map[sp.address, sp.string])
            self.data.messages = {}
            self.data.feedback = initial_message

        @sp.entrypoint
        def poke(self):
            # No message was sent, so use an empty string
            self.data.messages = sp.update_map(sp.sender, sp.Some(""), self.data.messages)

        @sp.entrypoint
        def pokeWithMessage(self, message: sp.string):
            # Include received message in storage
            self.data.messages = sp.update_map(sp.sender, sp.Some(message), self.data.messages)

        @sp.entrypoint
        def pokeOtherContract(self, targetAddress: sp.address):
            contract_opt = sp.contract(sp.unit, targetAddress, entrypoint="pokeMeBack")
            # Call the contract
            match contract_opt:
                case Some(contract):
                    sp.transfer((), sp.mutez(0), contract)
                case None:
                    sp.trace("Failed to find contract")

        @sp.entrypoint
        def pokeMeBack(self):
            # Call the same contract back
            contract_opt = sp.contract(sp.string, sp.sender, entrypoint="pokeWithMessage")
            match contract_opt:
                case Some(contract):
                    sp.transfer(self.data.feedback, sp.mutez(0), contract)
                case None:
                    sp.trace("Failed to find contract")


@sp.add_test()
def test():
    scenario = sp.test_scenario("poke_contract", main)
    contract = main.PokeContract("Hello")
    scenario += contract

    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")

    contract.poke(_sender=alice)
    contract.poke(_sender=bob)

    scenario.verify(contract.data.messages.get(alice.address) == "")
    scenario.verify(contract.data.messages.get(bob.address) == "")

    contract.pokeWithMessage("Hello", _sender=alice)
    scenario.verify(contract.data.messages.get(alice.address) == "Hello")

    contract2 = main.PokeContract("I poked you!")
    scenario += contract2

    contract.pokeOtherContract(contract2.address)
    scenario.verify(contract.data.messages.get(contract2.address) == "I poked you!")
