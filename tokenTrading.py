# pip install solana spl-token

import logging
import json
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.publickey import PublicKey
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer as token_transfer

# Configurar el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conexión a un nodo Solana (usar https://api.mainnet-beta.solana.com para mainnet)
client = Client("https://api.devnet.solana.com")

# Cargar claves privadas de manera segura (ejemplo básico, mejorar para producción)
def load_keypair_from_file(filepath):
    try:
        with open(filepath, 'r') as f:
            keypair_json = json.load(f)
        return Keypair.from_secret_key(bytes(keypair_json))
    except Exception as e:
        logger.error(f"Error loading keypair from file: {e}")
        raise

try:
    payer = load_keypair_from_file("path_to_payer_keypair.json")
    buyer = load_keypair_from_file("path_to_buyer_keypair.json")
    token_mint_address = PublicKey("YourTokenMintAddressHere")
except Exception as e:
    logger.error(f"Failed to load keypair or token mint address: {e}")
    raise

# Crear un cliente de token SPL
try:
    token_client = Token(client, token_mint_address, TOKEN_PROGRAM_ID, payer)
except Exception as e:
    logger.error(f"Failed to create token client: {e}")
    raise

# Obtener la cuenta asociada del token para el usuario (crearla si no existe)
def get_or_create_associated_token_account(owner_pubkey, token_mint_address):
    associated_account = token_client.get_associated_token_address(owner_pubkey)
    try:
        token_client.get_account_info(associated_account)
        logger.info(f"Associated token account for {owner_pubkey} found: {associated_account}")
    except Exception as e:
        logger.warning(f"Associated token account not found, creating a new one: {e}")
        try:
            tx = token_client.create_associated_token_account(owner_pubkey)
            client.send_transaction(tx, payer)
            logger.info(f"Associated token account created for {owner_pubkey}: {associated_account}")
        except Exception as e:
            logger.error(f"Failed to create associated token account: {e}")
            raise
    return associated_account

# Obtener las cuentas de token
try:
    payer_token_account = get_or_create_associated_token_account(payer.public_key, token_mint_address)
    recipient_public_key = PublicKey("RecipientPublicKeyHere")
    recipient_token_account = get_or_create_associated_token_account(recipient_public_key, token_mint_address)
except Exception as e:
    logger.error(f"Failed to get or create associated token accounts: {e}")
    raise

# Transacción para transferir tokens
def transfer_tokens(source_account, dest_account, owner, amount):
    tx = Transaction()
    try:
        tx.add(
            token_transfer(
                source=source_account,
                dest=dest_account,
                owner=owner,
                amount=amount
            )
        )
        response = client.send_transaction(tx, payer)
        logger.info(f"Transaction successful: {response}")
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        raise

# Ejemplo de venta de tokens
amount_to_sell = 10 * 10**9  # Por ejemplo, 10 tokens (asumiendo 9 decimales)
try:
    transfer_tokens(payer_token_account, recipient_token_account, payer.public_key, amount_to_sell)
except Exception as e:
    logger.error(f"Failed to sell tokens: {e}")

# Ejemplo de compra de tokens (similar al vender pero inverso)
amount_to_buy = 5 * 10**9  # Por ejemplo, 5 tokens (asumiendo 9 decimales)
try:
    buyer_token_account = get_or_create_associated_token_account(buyer.public_key, token_mint_address)
    transfer_tokens(recipient_token_account, buyer_token_account, recipient_public_key, amount_to_buy)
except Exception as e:
    logger.error(f"Failed to buy tokens: {e}")
