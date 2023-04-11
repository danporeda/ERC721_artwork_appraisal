import os
import json
from web3 import Web3
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from pinata import pin_file_to_ipfs, pin_json_to_ipfs, convert_data_to_json

load_dotenv()

# Define and connect a new Web3 provider
# Truffle suite Ganache blockchain: http://127.0.0.1:7545
w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI")))

################################################################################
# Contract Helper function:
################################################################################


@st.cache(allow_output_mutation=True)
def load_contract():

    # Load the contract ABI
    with open(Path('./contracts/compiled/artwork_abi.json')) as f:
        artwork_abi = json.load(f)

    contract_address = os.getenv("SMART_CONTRACT_ADDRESS")

    # Load the contract
    contract = w3.eth.contract(
        address=contract_address,
        abi=artwork_abi
    )

    return contract

contract = load_contract()

################################################################################
# Helper functions to pin files and json to Pinata
################################################################################
st.markdown("## Pin Artwork to IPFS")

def pin_artwork(artwork_name, artwork_file):

    # pin the file to IPFS with Pinata
    ipfs_file_hash = pin_file_to_ipfs(artwork_file.getvalue())

    # build a metadata file for the artwork
    token_json = {
        "name": artwork_name,
        "image": ipfs_file_hash
    }

    json_data = convert_data_to_json(token_json)

    json_ipfs_hash = pin_json_to_ipfs(json_data)

    return json_ipfs_hash


def pin_appraisal_report(report_content):
        report_json = convert_data_to_json(report_content)
        report_ipfs_hash = pin_json_to_ipfs(report_json)
        return report_ipfs_hash

################################################################################
# Register New Artwork
################################################################################
# Use a streamlit component to get the address of the artwork owner,
# artwork name, artist's name, and initial appraisal value.
st.title("Register New Artwork")
accounts = w3.eth.accounts
address = st.selectbox("Select Artwork Owner", options=accounts)
artwork_name = st.text_input("Enter the name of the artwork")
artist_name = st.text_input("Enter the artist name")
initial_appraisal_value = st.text_input("Enter the initial appraisal amount")
file = st.file_uploader("Upload Artwork", type=["jpeg", "jpg", "png"])
if st.button("Register Artwork"):
    ipfs_image_hash = pin_file_to_ipfs(file.getvalue())
    ipfs_metadata_hash = pin_artwork(artwork_name, file)
    artwork_uri = ipfs_image_hash
    # Use the contract to send a transaction to the registerArtwork function
    tx_hash = contract.functions.registerArtwork(
        address,
        artwork_uri,
        artwork_name,
        artist_name,
        int(initial_appraisal_value)
    ).transact({'from': address, 'gas': 1000000})
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    st.write("Transaction receipt mined:")
    st.write(dict(receipt))
    st.write("You can view the pinned metadata file with the following IPFS Gateway Link")
    st.markdown(f"[Artwork IPFS Gateway Link - JSON](https://ipfs.io/ipfs/{ipfs_metadata_hash})")
    st.markdown(f"[Artwork IPFS Gateway Link - Image File](https://ipfs.io/ipfs/{ipfs_image_hash})")

st.markdown("---")

################################################################################
# Appraise Art
################################################################################
st.markdown("## Appraise Artwork")
tokens = contract.functions.totalSupply().call()
token_id = st.selectbox("Choose an Art Token ID", list(range(tokens)))
new_appraisal_value = st.text_input("Enter the new appraisal amount")
report_uri = st.text_area("Enter notes about the appraisal")
if st.button("Appraise Artwork"):

    # Use the token_id and the report_uri to record the appraisal
    tx_hash = contract.functions.newAppraisal(
        token_id,
        int(new_appraisal_value),
        report_uri
    ).transact({"from": w3.eth.accounts[0]})
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    st.write(receipt)
st.markdown("---")

################################################################################
# Get Appraisals
################################################################################
st.markdown("## Get the appraisal report history")
total_supply = contract.functions.totalSupply()
art_token_id = st.number_input("Artwork ID: Tokens: 0 to {total_supply}", value=0, step=1)
if st.button("Get Appraisal Reports"):
    appraisal_filter = contract.events.Appraisal.createFilter(
        fromBlock=0,
        argument_filters={"tokenId": art_token_id}
    )
    appraisals = appraisal_filter.get_all_entries()
    if appraisals:
        for appraisal in appraisals:
            report_dictionary = dict(appraisal)
            st.markdown("### Appraisal Report Event Log")
            st.write(report_dictionary)
            st.markdown("### Appraisal Report Details")
            st.write(report_dictionary["args"])
    else:
        st.write("This artwork has no new appraisals")
    

    st.write("Pin an appraisal report")
    report_string = st.text_area("Paste Report String Here")
    if st.button("Pin Report"):
        report_hash = pin_appraisal_report(report_string)
        st.write(report_hash)

################################################################################
# Display a Token
################################################################################
st.markdown("## Display an Art Token")

selected_address = st.selectbox("Select Account", options=accounts)

tokens = contract.functions.balanceOf(selected_address).call()

st.write(f"This address owns {tokens} tokens")

token_list = []
for t in range(tokens):
    owners_token = contract.functions.tokenOfOwnerByIndex(selected_address, t).call()
    token_list.append(owners_token)

token_id = st.selectbox("Selected Address Artwork Tokens", token_list)

if st.button("Display"):

    # Use the contract's `tokenURI` function to get the art token's URI
    token_uri = contract.functions.tokenURI(token_id).call()
    st.write(f"The tokenURI is ipfs://{token_uri}")
    st.image(f"https://ipfs.io/ipfs/{token_uri}")


all_tokens = contract.functions.totalSupply().call()
token_select = st.selectbox("Browse All Tokens", list(range(all_tokens)))

if st.button("Open"):

    owner = contract.functions.ownerOf(token_select).call()
    st.write(f"The token is registered to {owner}")

    token_uri = contract.functions.tokenURI(token_select).call()
    st.image(f"https://ipfs.io/ipfs/{token_uri}")


