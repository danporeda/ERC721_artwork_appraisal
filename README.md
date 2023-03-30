# ERC721_artwork_appraisal

An app for registering artwork as an ER721 (NFT). The frontend is a Streamlit interface that has features to register new artwork, display NFT collections, see appraisals, and update artwork with new appraisals.

This app was developed to deploy to a testnet with prefunded signers (w3.eth.accounts), but the script can be easily modified to deploy to the ethereum main net, with input of custom addresses. 

After cloning this repository, deploy the contract Artwork.sol. Then create a .env file in the repository with: WEB3_PROVIDER_URI="", and SMART_CONTRACT_ADDRESS="". Fill these values with the URI of your chosen blockchain, and the deployed contract's address. 

You will need Streamlit to run the app. Once installed, open your CLI to the repository path, and enter: streamlit run app.py
