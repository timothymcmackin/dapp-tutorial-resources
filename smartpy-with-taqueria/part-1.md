---
title: 'Part 1: Creating a simple dApp'
authors: 'Benjamin Fuentes (Marigold), Tim McMackin'
last_update:
  date: 30 Jan 2026
dependencies:
  smartpy: 0.24.0
  vite: 7.2.4
  taquito: 0
---

To start working with the application, you create a Taqueria project and use it to deploy a basic version of the Poke smart contract.
Then you set up a web application to connect with a wallet and interact with your smart contract.

Before you begin, make sure that you have installed the tools in the [Prerequisites](/tutorials/dapp#prerequisites) section.

## Creating a smart contract in a Taqueria project

Taqueria is a development environment that manages the project structure and keeps it up to date.
For example, as you work on developing applications, Taqueria remembers the addresses of the contracts that you have deployed to different environments.

Follow these steps to set up a Taqueria project:

On the command-line terminal, run these commands to set up a Taqueria project and install the LIGO and Taquito plugins:

```bash
taq init pokeGame
cd pokeGame
taq install @taqueria/plugin-ligo
taq install @taqueria/plugin-taquito
taq install @taqueria/plugin-octez-client
taq create contract pokeGame.jsligo
```

These commands create a Taqueria project, install the plugins that let you use Taquito, JsLIGO, and the Octez command-line client for Tezos in it, and create a placeholder contract file.

### Writing the smart contract

Smart contracts are backend programs with specific restrictions that allow them to be transparent, immutable, trustless, and censorship-proof.
Tezos smart contracts have one or more [entrypoints](/smart-contracts/entrypoints) that clients can call, similar to the endpoints in an API.
The smart contract also has dedicated storage that no other program can change.
For more information about smart contracts, see [An introduction to smart contracts](/smart-contracts).

The smart contract that you create in this section is very simple: it allows users to "poke" it by sending a simple transaction.
It keeps track of the addresses of the users who have poked it.
In later parts of this tutorial, you enhance the contract to respond when it gets poked, but for now all the contract does is record who has called it.

Edit the `pokeGame.jsligo` file to remove the default code and paste this code instead:

```jsligo
import Tezos = Tezos.Next;

export type storage = set<address>;

type return_type = [list<operation>, storage];

export namespace PokeGame {

  // Accept a poke and store the sender's address
  @entry
  const poke = (_: unit, storage: storage): return_type =>
    [[], Set.add(Tezos.get_sender(), storage)];

}
```

This contract code is in the JsLIGO language, which is based on JavaScript/TypeScript.
First, it defines two types that are used later:

  - The type of the storage for the contract, which in this case is a [set](/smart-contracts/data-types/complex-data-types#sets) data type that contains the addresses of the accounts that have called the contract.

  - The return type that all entrypoints must have: a list of operations to run next and the new state of the contract storage.

The `poke` function is an [entrypoint](/smart-contracts/entrypoints), a function that external accounts can call.
Every contract must have at least one entrypoint, annotated with `@entry`.
Entrypoints must accept two arguments: the parameter that the client passes and the current state of the storage.
This parameter can be many different things, but in this case, the caller passes no value, which is represented by the "unit" type.
In this case, the function uses the function `Tezos.get_sender()` to get the address of the caller and the function `Set.add` to add it to the storage.

For more information about LIGO code, see https://ligo.tezos.com.

:::note

Using a set data type here introduces a security flaw into the contract.
The set can grow to an arbitrarily large size, and at some point, become too big to load in a single operation.
At this point, the contract becomes unusable.

It's fine for this tutorial because the set can become very large before this happens, but contracts in production environments must limit the scope of their storage either by placing limits on unbounded types or by using big-maps or big-sets, which are lazy-loaded.
For more information, see [Smart contract security](https://ligo.tezos.com/docs/next/tutorials/security/?lang=jsligo) in the LIGO documentation or the tutorial [Security](/tutorials/security).

:::

Now you can use Taqueria to simulate calling the contract to make sure it works before you deploy it.

### Simulating a call to the smart contract

The LIGO command-line client provides commands to test LIGO code.

1. Run this command to compile the contract with Taqueria:

   ```bash
   taq compile pokeGame.jsligo
   ```

   If compilation is successful, Taqueria generates these files:

   - `artifacts/pokeGame.tz`: The compiled Michelson code of the contract, which is the code you will actually deployed to Tezos.
   Michelson is a stack-based language and difficult to read, so most developers use languages such as JsLIGO to write it.
   For more information about these higher-level languages, see [Languages](/smart-contracts/languages).

   - `contracts/pokeGame.storageList.jsligo`: You can use this file to set the state of the contract storage when you deploy the contract.
   As it stands now, you probably want to deploy the contract with an empty set, but if the starting storage is complicated, you can set it in this file and use it when you deploy the contract.

   - `pokeGame.parameterList.jsligo`: This file defines the parameters that the contract accepts.
   This file can be useful to assemble complex parameters for testing.

1. Set the starting storage to be an empty set of addresses by replacing the `contracts/pokeGame.storageList.jsligo` file with this code:

   ```jsligo
   #import "pokeGame.jsligo" "Contract"

   const default_storage: Contract.storage = Set.empty as set<address>;
   ```

   This code defines the initial storage as an empty set by calling the LIGO function `Set.empty`.
   It also ensures that the type of this value matches the storage type of the contract by applying the type annotation `Contract.storage`.

1. Compile the contract again by running this command:

   ```bash
   taq compile pokeGame.jsligo
   ```

   This command now compiles the contract with awareness of the initial storage.
   Note that the Taqueria response now includes both the contract file and the storage file:

   ```log
   ┌─────────────────┬───────────────────────────────────────┐
   │ Source          │ Artifact                              │
   ├─────────────────┼───────────────────────────────────────┤
   │ pokeGame.jsligo │ artifacts/pokeGame.tz                 │
   │                 │ artifacts/pokeGame.default_storage.tz │
   └─────────────────┴───────────────────────────────────────┘
   ```

1. Edit the second file `pokeGame.parameterList.jsligo` to have this code:

   ```jsligo
   #import "pokeGame.jsligo" "Contract"

   const default_parameter: parameter_of Contract.PokeGame = Poke();
   ```

   This code creates a type that represents the parameter that clients pass to the contract.
   You use this parameter to build simulated calls to the contract for testing purposes.

1. Compile the contract and the related files again:

   ```bash
   taq compile pokeGame.jsligo
   ```

   The response includes the three Michelson files in the `artifacts` folder that correspond to the JsLIGO source files in the `contracts` folder.

1. Simulate a call to the contract by running this command:

   ```bash
   taq simulate pokeGame.tz --param pokeGame.parameter.default_parameter.tz
   ```

   This command simulates deploying the contract with the storage in the storage file and then calling the contract with a parameter generated based on the parameter file.
   The response shows the new state of the contract storage (a set with a single address in it) and the operations that the contract created (none in this case).
   The response also shows `big_map diff`, which lists the updates to a different kind of storage called a big-map; the contract does not use big-maps so there are no updates in this case.

   ```log
   ┌─────────────┬──────────────────────────────────────────────┐
   │ Contract    │ Result                                       │
   ├─────────────┼──────────────────────────────────────────────┤
   │ pokeGame.tz │ storage                                      │
   │             │   { "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU" } │
   │             │ emitted operations                           │
   │             │                                              │
   │             │ big_map diff                                 │
   │             │                                              │
   │             │                                              │
   └─────────────┴──────────────────────────────────────────────┘
   ```

   This simulation shows that the `poke` entrypoint works because it records the address of the account that called it in the contract storage.

### Deploying the contract to a test network

Before you deploy the contract to Tezos Mainnet, you can deploy it to the test network named Ghostnet.
By default, Taqueria projects are configured to use Ghostnet.
Test networks have programs called _faucets_ that give you some tez tokens that you can use to pay for transaction fees for deploying and calling contracts on the testnet.

1. Attempt to deploy the contract to the test network by running this command:

   ```bash
   taq deploy pokeGame.tz -e "testing"
   ```

   The `-e "testing"` argument corresponds to the default definition of the Ghostnet testnet in the Taqueria configuration file `.taq/config.json`:

   ```json
   "testing": {
       "type": "simple",
       "label": "ghostnet",
       "rpcUrl": "https://ghostnet.ecadinfra.com"
   },
   ```

   This command fails because you don't have an account set up in Taqueria.
   Taqueria creates an account for you to use locally and prints the address of the account, as in this example:

   ```log
   A keypair with public key hash tz1XXXXXXXXXXXXXXXXXXXXXX was generated for you.
   ```

   Full information including the private key of the account is in the file `.taq/config.local.testing.json`.

1. Fund the account with a small amount of tez to pay the transaction fees to deploy the contract:

   1. Go to the Ghostnet faucet page at https://faucet.ghostnet.teztnets.com.

   1. On the faucet page, paste the address into the input field labeled "Or fund any address" and click the button for the amount of tez to add to your wallet.
   20 tez is enough to work with the tutorial contract, and you can return to the faucet later if you need more tez.

      It may take a few minutes for the faucet to send the tokens.

      You can use the faucet as much as you need to get tokens on the testnet, but those tokens are worthless and cannot be used on Mainnet.

      ![Fund your wallet using the Ghostnet Faucet](/img/tutorials/wallet-funding.png)

1. Run the deployment command again:

   ```bash
   taq deploy pokeGame.tz -e "testing"
   ```

   This time, Taqueria should deploy the contract successfully.
   If so, it prints the address of the deployed contract to the log:

   ```log
   ┌─────────────┬──────────────────────────────────────┬──────────┐
   │ Contract    │ Address                              │ Alias    │
   ├─────────────┼──────────────────────────────────────┼──────────┤
   │ pokeGame.tz │ KT1RbYvyvBD3WkcNY8UXwCsbLERAougeSFsf │ pokeGame │
   └─────────────┴──────────────────────────────────────┴──────────┘
   ```

Now the contract is deployed to the test network and clients can call it.
You can see information about the contract by looking it up on a block explorer such as https://ghostnet.tzkt.io by this address.
In the next section, you create a simple web application to call it.

## Creating the frontend

The frontend that you create in this section includes basic features to connect to a user's wallet and get information about their account.
Then you add features to search for contracts that are similar to your poke contract and send poke transactions to them.

Before you start, make sure that you have a Tezos wallet installed in a web browser so you can connect to the frontend and have some testnet tez.
You can use a different account in this wallet than you used to deploy the contract.
See [Installing and funding a wallet](/developing/wallet-setup).

### Creating a React application

These steps show you how to create a simple React application to act as the frontend for the dApp.
This application uses Taquito and related tools to connect to user wallets to show their balances.
It also uses the API of the [TzKT.io](https://tzkt.io/) indexer to search for contracts.

1. From the same location as the `pokeGame` Taqueria project, use `yarn` to create a web application with Vite, a JavasScript framework:

   ```bash
   yarn create vite
   ```

1. Follow the prompts to create the application:

   1. For the project name and package name, specify `frontend`.

   1. For the framework, specify `React`.

   1. For the variant, select `TypeScript + SWC`.

   1. For `Use rolldown-vite (Experimental)?`, select `No`.

   1. For `Install with yarn and start now?`, select `No`.

1. Add the Taquito and TzKT indexer libraries:

   ```bash
   cd frontend
   yarn add @taquito/taquito @taquito/beacon-wallet @airgap/beacon-sdk @tzkt/sdk-api
   yarn add -D @airgap/beacon-types
   ```

1. Add the following dependencies in order to resolve polyfill issues.
Some dependencies are from Node.JS and therefore are not included in browsers:

   ```bash
   yarn add --dev process buffer crypto-browserify stream-browserify assert stream-http https-browserify os-browserify url path-browserify
   ```

1. Open the `index.html` file and replace the `body` with this code:

   ```html
   <body>
     <div id="root"></div>
     <script type="module" src="/src/nodeSpecific.ts"></script>
     <script type="module" src="/src/main.tsx"></script>
   </body>
   ```

1. Open the `vite.config.ts` file and replace it with this code:

   ```js
   import react from '@vitejs/plugin-react-swc';
   import path from 'path';
   import { defineConfig } from 'vite';
   // https://vitejs.dev/config/
   export default ({ command }) => {
     const isBuild = command === 'build';

     return defineConfig({
       plugins: [react()],
       define: {
         'process.version': JSON.stringify("20.19.4"),
       },
       build: {
         commonjsOptions: {
           transformMixedEsModules: true,
         },
       },
       resolve: {
         alias: {
           // dedupe @airgap/beacon-sdk
           // I almost have no idea why it needs `cjs` on dev and `esm` on build, but this is how it works 🤷‍♂️
           '@airgap/beacon-sdk': path.resolve(
             path.resolve(),
             `./node_modules/@airgap/beacon-sdk/dist/${
               isBuild ? 'esm' : 'cjs'
             }/index.js`
           ),
           stream: 'stream-browserify',
           os: 'os-browserify/browser',
           util: 'util',
           process: 'process/browser',
           buffer: 'buffer',
           crypto: 'crypto-browserify',
           assert: 'assert',
           http: 'stream-http',
           https: 'https-browserify',
           url: 'url',
           path: 'path-browserify',
         },
       },
     });
   };
   ```

1. Create a new file named `nodeSpecific.ts` in the `src` folder of the `frontend` project and edit with this content:

   ```js
   import "./init";
   import { Buffer } from 'buffer';

   globalThis.Buffer = Buffer;
   ```

   TODO do I need to add `init` to `Main.tsx`?

### Generating the Typescript classes from Michelson code and run the server

Taqueria is able to generate Typescript classes for any frontend application.
It takes the definition of your smart contract and generates the contract entrypoint functions, type definitions, and other code that you can use in TypeScript.

1. From the root folder of the project, run these commands to generate the TypeScript classes:

   ```bash
   taq install @taqueria/plugin-contract-types
   taq generate types ./frontend/src
   ```

1. Go back to your frontend app and run the dev server.

   ```bash
   cd frontend
   yarn dev
   ```

1. Open the web application in a web browser at http://localhost:5173.

The page shows the default Vite application, which you will configure in the next section to act as the frontend for your dApp.

### Connecting to the wallet

In this section, you add React Button components to trigger the connection to the wallet and text fields that display the user's address and balance.

1. Add a file named `src/init.ts` with this code:

   ```js
   window.global ||= window;
   ```

1. Replace the `src/App.tsx` file with this code:

   ```js
   import "./init";
   import { NetworkType } from '@airgap/beacon-types';
   import { BeaconWallet } from '@taquito/beacon-wallet';
   import { TezosToolkit } from '@taquito/taquito';
   import * as api from '@tzkt/sdk-api';
   import { useEffect, useState } from 'react';
   import './App.css';
   import ConnectButton from './ConnectWallet';
   import DisconnectButton from './DisconnectWallet';

   function App() {
     api.defaults.baseUrl = 'https://api.ghostnet.tzkt.io';

     const [Tezos, setTezos] = useState<TezosToolkit>(
       new TezosToolkit('https://rpc.ghostnet.teztnets.com')
     );
     const [wallet, setWallet] = useState<BeaconWallet>(
       new BeaconWallet({
         name: 'Poke game',
         network: {
           type: NetworkType.GHOSTNET,
         }
       })
     );
     Tezos.setWalletProvider(wallet);

     useEffect(() => {
       (async () => {
         const activeAccount = await wallet.client.getActiveAccount();
         if (activeAccount) {
           setUserAddress(activeAccount.address);
           const balanceMutez = await Tezos.tz.getBalance(activeAccount.address);
           const balanceTez = balanceMutez.toNumber() / 10000000;
           setUserBalance(balanceTez);
         }
       })();
     }, []);

     const [userAddress, setUserAddress] = useState<string>('');
     const [balanceTez, setUserBalance] = useState<number>(0);

     return (
       <div className="App">
         <header className="App-header">
           <ConnectButton
             Tezos={Tezos}
             setTezos={setTezos}
             setUserAddress={setUserAddress}
             setUserBalance={setUserBalance}
             wallet={wallet}
           />

           <DisconnectButton
             wallet={wallet}
             setUserAddress={setUserAddress}
             setUserBalance={setUserBalance}
           />

           <div>
             {userAddress ?
                 `I am ${userAddress} with ${balanceTez} tez`
               : `Click "Connect with wallet."`
             }
           </div>
         </header>
       </div>
     );
   }

   export default App;
   ```

   If you look at the page in the web browser, it throws an error because files it references don't exist yet.

   These components will be buttons that connect to or disconnect from the user's wallet.

1. Put this code in a file named `src/ConnectWallet.tsx`:

   ```js
   import "./init";
   import { NetworkType } from "@airgap/beacon-sdk";
   import { BeaconWallet } from "@taquito/beacon-wallet";
   import { TezosToolkit } from "@taquito/taquito";
   import { Dispatch, SetStateAction } from "react";

   type ButtonProps = {
     Tezos: TezosToolkit;
     setUserAddress: Dispatch<SetStateAction<string>>;
     setUserBalance: Dispatch<SetStateAction<number>>;
     wallet: BeaconWallet;
     setTezos: Dispatch<SetStateAction<TezosToolkit>>;
   };
   const ConnectButton = ({
     Tezos,
     setTezos,
     setUserAddress,
     setUserBalance,
     wallet,
   }: ButtonProps): JSX.Element => {
     const connectWallet = async (): Promise<void> => {
       try {
         await wallet.requestPermissions();
         // gets user's address
         const userAddress = await wallet.getPKH();
         const balanceMutez = await Tezos.tz.getBalance(userAddress);
         const balanceTez = balanceMutez.toNumber() / 10000000;
         setUserBalance(balanceTez);
         setUserAddress(userAddress);

         Tezos.setWalletProvider(wallet);
         setTezos(Tezos);
       } catch (error) {
         console.log(error);
       }
     };
     return (
       <div className="buttons">
         <button className="button" onClick={connectWallet}>
           <span>
             <i className="fas fa-wallet"></i>&nbsp; Connect with wallet
           </span>
         </button>
       </div>
     );
   };
   export default ConnectButton;

   ```

   This file uses Taquito's `wallet.requestPermissions` function to prompt the user to connect to the site.
   Then it gets information about the account, including its address and tez balance.

1. Put this code in the `DisconnectWallet.tsx` file:

   ```js
   import { BeaconWallet } from '@taquito/beacon-wallet';
   import { Dispatch, SetStateAction } from 'react';

   interface ButtonProps {
     wallet: BeaconWallet;
     setUserAddress: Dispatch<SetStateAction<string>>;
     setUserBalance: Dispatch<SetStateAction<number>>;
   }

   const DisconnectButton = ({
     wallet,
     setUserAddress,
     setUserBalance,
   }: ButtonProps): JSX.Element => {
     const disconnectWallet = async (): Promise<void> => {
       setUserAddress('');
       setUserBalance(0);
       console.log('disconnecting wallet');
       await wallet.clearActiveAccount();
     };

     return (
       <div className="buttons">
         <button className="button" onClick={disconnectWallet}>
           <i className="fas fa-times"></i>&nbsp; Disconnect wallet
         </button>
       </div>
     );
   };

   export default DisconnectButton;
   ```

   The button cleans the wallet instance and all linked objects.
   It's good practice to make it easy for the user to disconnect so they can reconnect with a different account.

1. Save both files and open the new page in your web browser.

1. Test the wallet connection:

   1. Click **Connect with wallet**.

   1. In the popup, select your wallet and account and in the wallet, allow it to connect to the web application.

   The page shows your address and account balance:

   ![The app after you have connected, showing your address and tez balance](/img/tutorials/dapp-connected.png)

1. Click **Disconnect wallet** to test the disconnection, and then reconnect.

Now you can connect to user wallets.
This example application uses the Beacon protocol, which can connect to many different Tezos-compatible wallets.

### Listing other poke contracts via an indexer

Listing all poke contracts on the network would take a lot of requests to the RPC node.
You might have to query every block looking for contracts that are similar to yours.

In this section, you use a better way to get information about the network: an indexer.
An indexer is a kind of enriched cache API that provides information about the network in a format that is more useful to off-chain applications.
This example uses the TzKT.io indexer to search for contracts:

1. [Install the `jq` program](https://github.com/stedolan/jq), which is needed to parse the Taqueria JSON configuration file.

1. In the `package.json` file of the frontend application, change the `dev` command in the `scripts` section to this code:

   ```bash
   "dev": "jq -r '\"VITE_CONTRACT_ADDRESS=\" + last(.tasks[]).output[0].address' ../pokeGame/.taq/testing-state.json > .env && vite",
   ```

   This command uses the `jq` program to get the most recently deployed contract from the Taqueria configuration and set it as an environment variable for the frontend to use.


   :::note

   You may need to change the path to this file in the command to point to your Taqueria project.

   :::

1. Edit the `App.tsx` file and add this code immediately before the `return` statement:

   ```js
   const [contracts, setContracts] = useState<Array<api.Contract>>([]);

   const fetchContracts = () => {
     (async () => {
       setContracts(
         await api.contractsGetSimilar(import.meta.env.VITE_CONTRACT_ADDRESS, {
           includeStorage: true,
           sort: { desc: 'id' },
         })
       );
     })();
   };
   ```

   This function uses the TzKT API to get contracts with the same interface (parameter and storage) as yours.

1. After the `<div>` tag that shows the user's address and balance, add this code:

   ```tsx
   <br />
   <button onClick={fetchContracts}>Fetch contracts</button>
   <table>
     <thead>
       <tr>
        <th>Contract address</th>
        <th>Pokes and messages</th>
        <th>Actions</th>
       </tr>
     </thead>
     <tbody>
       {contracts.map((contract, index) => <tr key={index}><td style={{borderStyle: "dotted"}}>{contract.address}</td><td style={{borderStyle: "dotted"}}>{contract.storage.join(", ")}</td><td style={{borderStyle: "dotted"}}></td></tr>)}
     </tbody>
   </table>
   ```

   This button calls the function from the previous step and shows the returned contracts in a table.

1. Save the file and restart the server.
   Now, the start script generates the `.env` file containing the last deployed contract address.

   ```bash
   yarn dev
   ```

1. Open the application in a web browser again and click **Fetch contracts**.
   The application shows the addresses of contracts that are similar to yours, as shown in this screencap:

   ![The application showing a connected wallet and a list of matching contracts](/img/tutorials/dapp-deployedcontracts.png)

   If there are too many contracts, you can add a `limit` parameter next to the `sort` and `includeStorage` parameters to limit the number of contracts returned.

Now you can query for contracts that are similar to yours.

### Showing more information

You can use the indexer to get information from each contract, such as the addresses that have poked each contract.
In this section, you add this information and put in a button that allows users to poke each contract.
You also use the Taqueria-generated types to specify the type of the data in the contracts, making it easier to work with the contracts' storage.

1. Add this line at the top of the `src/App.tsx` file to import the Taqueria-generated types:

   ```typescript
   import { type PokeGameWalletType } from './pokeGame.types';
   ```

1. Add this new function after the `fetchContracts` function:

   ```typescript
   const poke = async (contract: api.Contract) => {
     let c: PokeGameWalletType = await Tezos.wallet.at<PokeGameWalletType>(
       '' + contract.address
     );
     try {
       const op = await c.methodsObject.default().send();
       await op.confirmation();
       alert('Tx done');
     } catch (error: any) {
       console.table(`Error: ${JSON.stringify(error, null, 2)}`);
     }
   };
   ```

   This function calls a poke contract via the user's wallet.

   :::note

   This function calls the `default` entrypoint of the contract instead of the `poke` entrypoint.
   This is because when a contract has only one entrypoint, it becomes the "default" entrypoint.
   For more information, see [Implementation details: the default entrypoint](smart-contracts/entrypoints#implementation-details-the-default-entrypoint).

   Also, be careful because all entrypoint function names are in lowercase, and all parameter types are in uppercase.

   :::

1. Replace the `<tbody>` tag with this code:

   ```html
   <tbody>
     {contracts.map((contract, index) => <tr key={index}><td style={{borderStyle: "dotted"}}>{contract.address}</td><td style={{borderStyle: "dotted"}}>{contract.storage.join(", ")}</td><td style={{borderStyle: "dotted"}}><button onClick={() => poke(contract)}>Poke</button></td></tr>)}
   </tbody>
   ```

   This update adds a **Poke** button for each contract that calls the function that creates the transaction.
   It also shows a list of the addresses that have poked each contract.

   The page looks like this:

   ![The updated page showing a list of addresses and a button next to each contract address](/img/tutorials/dapp-pokecontracts.png)

1. Click one of the **Poke** buttons, approve the transaction in your wallet, and wait for a popup that shows the message "Tx done."

1. Click **Fetch contracts** again and verify that your address is listed next to the contract that you poked, as in this example:

   ![The updated page showing that an account has poked the first contract](/img/tutorials/dapp-pokecontracts-poked.png)

   It may take a few seconds for the transaction to be confirmed on Tezos and for TzKT to update its information.

## Summary

In this section, you learned to:

- Create a smart contract in the JsLIGO language
- Deploy it with Taqueria
- Create a complete dApp frontend with the Taquito SDK, including connecting to a user's wallet and prompting them to send transactions
- Querying complex information about smart contracts from TzKT

In the next section, you learn how to call a smart contract from another smart contract.
You also write unit and mutation tests.

When you are ready, continue to [Part 2: Inter-contract calls and testing](/tutorials/dapp/part-2).
