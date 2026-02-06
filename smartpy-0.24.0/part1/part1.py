import smartpy as sp

@sp.module
def main():
    class PokeContract(sp.Contract):
        def __init__(self):
            sp.cast(self.data.received_pokes, sp.set[sp.address])
            self.data.received_pokes = set()

        @sp.entrypoint
        def poke(self):
            self.data.received_pokes.add(sp.sender)

@sp.add_test()
def test():
    scenario = sp.test_scenario("poke_contract", main)
    contract = main.PokeContract()
    scenario += contract

    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")

    contract.poke(_sender=alice)
    contract.poke(_sender=bob)

    scenario.verify(contract.data.received_pokes.contains(alice.address))
    scenario.verify(contract.data.received_pokes.contains(bob.address))


