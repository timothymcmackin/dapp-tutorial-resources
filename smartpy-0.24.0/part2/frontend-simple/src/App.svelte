<script>
  import { BeaconWallet } from "@taquito/beacon-wallet";
  import { NetworkType } from "@airgap/beacon-types";
  import { ContractAbstraction, TezosToolkit } from "@taquito/taquito";
  import * as api from '@tzkt/sdk-api';

  const rpcUrl = "https://rpc.shadownet.teztnets.com";
  api.defaults.baseUrl = 'https://api.shadownet.tzkt.io';
  const Tezos = new TezosToolkit(rpcUrl);
  // const myPokeContract = 'KT1PgwpEpHUi3AJ9L5E5x2CN69i4nGqDn7iB'; // Part 1
  const myPokeContract = "KT1DJVyq2myNVSsDaMMnsq6BwBoXjntPtGLu"; // Part 2

  let wallet;
  let address;
  let matchingContracts = [];
  let enteredContract;

  const connectWallet = async () => {
    const newWallet = new BeaconWallet({
      name: "Poke game dApp",
      network: {
      type: NetworkType.SHADOWNET,
    },
    });
    await newWallet.requestPermissions();
    address = await newWallet.getPKH();
    wallet = newWallet;
    Tezos.setWalletProvider(wallet);
  }

  const disconnectWallet = () => {
    wallet.client.clearActiveAccount();
    wallet = undefined;
  }

  const getContracts = async () => {
    matchingContracts = await api.contractsGetSimilar(
      myPokeContract,
      {
        includeStorage: true,
        sort: { desc: 'id' },
      }
    );
  }

  const pokeContract = async (targetAddress) => {
    const targetContract = await Tezos.wallet.at(targetAddress);
    try {
      const op = await targetContract.methodsObject.poke().send();
      console.log(`Waiting for ${op.opHash} to be confirmed...`);
      await op.confirmation(2);
      await getContracts();
    } catch (error) {
      console.error(error);
    }
  }

  const pokeOtherContract = async (sourceAddress, targetAddress) => {
    const sourceContract = await Tezos.wallet.at(sourceAddress);
    try {
      const op = await sourceContract.methodsObject.pokeOtherContract(targetAddress).send();
      console.log(`Waiting for ${op.opHash} to be confirmed...`);
      await op.confirmation(2);
      await getContracts();
    } catch (error) {
      console.error(error);
    }
  }


</script>

<main>
  <h1>Poke game dApp</h1>

<div class="card">
   {#if wallet}
    <p>The address of the connected wallet is {address}.</p>
    <p>
      <button on:click={disconnectWallet}> Disconnect wallet </button>
    </p>
   {:else}
    <button on:click={connectWallet}> Connect wallet </button>
   {/if}
   <button on:click={getContracts}> Refresh contracts </button>
   {#if matchingContracts.length > 0}
   <table>
    <thead>
      <tr>
        <th>Contract address</th>
        <th>Pokes and messages</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#each matchingContracts as oneContract}
      <tr>
        <td>{oneContract.address}<br /> {oneContract.storage.feedback}</td>
        <td>{Object.keys(oneContract.storage.messages).map((oneKey) => oneKey + ': ' + oneContract.storage.messages[oneKey]).join('\n')}</td>
        <td>
          <button on:click={() => pokeContract(oneContract.address)}> Poke </button>
          <input bind:value={enteredContract} />
          <button on:click={() => pokeOtherContract(oneContract.address, enteredContract)}> Poke from contract</button>
        </td>
      </tr>
      {/each}
    </tbody>
  </table>
   {/if}
</div>
</main>

<style>
  td {
    border-width: 1px;
    border-color: white;
    border-style: solid;
    padding: 5px;
  }
</style>