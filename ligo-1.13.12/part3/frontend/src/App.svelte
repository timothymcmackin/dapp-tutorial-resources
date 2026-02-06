<script>
  import { BeaconWallet } from "@taquito/beacon-wallet";
  import { NetworkType } from "@airgap/beacon-types";
  import { TezosToolkit } from "@taquito/taquito";
  import * as api from '@tzkt/sdk-api';

  const rpcUrl = "https://rpc.shadownet.teztnets.com";
  api.defaults.baseUrl = 'https://api.shadownet.tzkt.io';
  const Tezos = new TezosToolkit(rpcUrl);
  const myPokeContract = 'KT19rzVSo3xqcDAW8sso6snMdvURgqQ2AATe';

  let wallet;
  let address;
  let matchingContracts = [];
  let feedbackContract;

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
    console.log("Calling", feedbackContract)
    try {
      const op = await targetContract.methodsObject.pokeAndGetFeedback(feedbackContract).send();
      console.log(`Waiting for ${op.opHash} to be confirmed...`);
      await op.confirmation(2);
      await getContracts();
    } catch (error) {
      console.error(error);
    }
  }

const createTicket = async (targetAddress) => {
  const targetContract = await Tezos.wallet.at(targetAddress);
  try {
    const op = await targetContract.methodsObject.createTicket(address).send();
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
        <td>{oneContract.address}</td>
        <td><ul>
          {#each Object.keys(oneContract.storage.messages) as oneAddress}
            <li>{oneAddress}: {oneContract.storage.messages[oneAddress]}</li>
          {/each}
        </ul></td>
        <td>
          <input bind:value={feedbackContract} />
          <button on:click={() => pokeContract(oneContract.address)}> Poke </button>
          <button on:click={() => createTicket(oneContract.address)}> Create ticket </button>
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
