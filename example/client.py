import os
import requests
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

USER_ONE_HOST = os.environ.get('USER_ONE_HOST', 'http://flash_one:3000/flash')
USER_ONE_SETTLEMENT = 'USERONE9ADDRESS9USERONE9ADDRESS9USERONE9ADDRESS9USERONE9ADDRESS9USERONE9ADDRESS9U'
USER_TWO_HOST = os.environ.get('USER_TWO_HOST', 'http://flash_two:3000/flash')
USER_TWO_SETTLEMENT = 'USERTWO9ADDRESS9USERTWO9ADDRESS9USERTWO9ADDRESS9USERTWO9ADDRESS9USERTWO9ADDRESS9U'

SECURITY = 2
TREE_DEPTH = 3
SIGNERS_COUNT = 2
BALANCE = 4000
DEPOSIT = [2000, 2000]


class FlashClient:

    def __init__(self, url, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password
        self.channel_id = None

    def init(self, **kwargs):
        response = self._post(path='/init', **kwargs)
        self.channel_id = response['channelId']
        return response['flash']

    def multisignature(self, **kwargs):
        return self._post(path='/multisignature/' + self.channel_id, **kwargs)

    def settlement(self, **kwargs):
        return self._post(path='/settlement/' + self.channel_id, **kwargs)

    def transfer(self, **kwargs):
        return self._post(path='/transfer/' + self.channel_id, **kwargs)

    def sign(self, **kwargs):
        return self._post(path='/sign/' + self.channel_id, **kwargs)

    def apply(self, **kwargs):
        return self._post(path='/apply/' + self.channel_id, **kwargs)

    def close(self, **kwargs):
        return self._post(path='/close/' + self.channel_id, **kwargs)

    def fund(self, **kwargs):
        return self._post(path='/fund/' + self.channel_id, **kwargs)

    def finalize(self, **kwargs):
        return self._post(path='/finalize/' + self.channel_id, **kwargs)

    def _post(self, path, **kwargs):
        auth = (self.username, self.password) if self.username else None
        response = requests.post(self.url + path, json=kwargs, auth=auth)
        if response.status_code >= 400:
            logger.info(response.text)
        response.raise_for_status()
        return response.json()


# noinspection PyUnusedLocal
def main():
    client_one = FlashClient(url=USER_ONE_HOST, username='user_one', password='password_one')
    client_two = FlashClient(url=USER_TWO_HOST, username='user_two', password='password_two')

    ##########################################################
    # Step 1: Initialise Flash channel
    ##########################################################
    logger.info('############# Initializing Flash channel #############')
    user_one_flash = client_one.init(userIndex=0, security=SECURITY, depth=TREE_DEPTH,
                                     signersCount=2, balance=BALANCE, deposit=DEPOSIT)
    user_two_flash = client_two.init(userIndex=1, security=SECURITY, depth=TREE_DEPTH,
                                     signersCount=2, balance=BALANCE, deposit=DEPOSIT)

    ##########################################################
    # Step 2: Generate multisignature addresses
    ##########################################################
    logger.info('############# Generating multisignature addresses #############')
    all_digests = [user_one_flash['partialDigests'], user_two_flash['partialDigests']]
    client_one.multisignature(allDigests=all_digests)
    client_two.multisignature(allDigests=all_digests)

    ##########################################################
    # Step 3: Set settlement addresses
    ##########################################################
    logger.info('############# Setting settlement addresses #############')
    settlement_addresses = [USER_ONE_SETTLEMENT, USER_TWO_SETTLEMENT]
    user_one_flash = client_one.settlement(settlementAddresses=settlement_addresses)
    user_two_flash = client_two.settlement(settlementAddresses=settlement_addresses)

    ##########################################################
    # Step 4: Fund channel
    ##########################################################
    # logger.info('############# Funding channel #############')
    # transactions_one = client_one.fund()
    # transactions_two = client_two.fund()
    # # ...wait for transactions to be confirmed
    # logger.info('Fund channel: {}, {}'.format(transactions_one, transactions_two))

    ##########################################################
    # Step 5: Transfer IOTA within channel
    ##########################################################
    logger.info('############# Initiating transfer #############')
    transfers = [{'value': 200, 'address': USER_TWO_SETTLEMENT}]
    bundles = client_one.transfer(transfers=transfers)

    ##########################################################
    # Step 6: Sign bundles
    ##########################################################
    logger.info('############# Signing bundles #############')
    signed_bundles = client_one.sign(bundles=bundles)
    signed_bundles = client_two.sign(bundles=signed_bundles)

    ##########################################################
    # Step 7: Applying signed bundles to Flash object
    ##########################################################
    logger.info('############# Applying signed bundles #############')
    user_one_flash = client_one.apply(signedBundles=signed_bundles)
    user_two_flash = client_two.apply(signedBundles=signed_bundles)

    ##########################################################
    # Step 8: Performing multiple transactions
    ##########################################################
    num_transactions = 2 ** (TREE_DEPTH + 1) - 2  # minus first and closing transaction
    for transaction_count in range(num_transactions):
        logger.info('############# Performing transaction {} #############'.format(transaction_count))
        transfers = [{'value': 1, 'address': USER_TWO_SETTLEMENT}]
        bundles = client_one.transfer(transfers=transfers)
        signed_bundles = client_one.sign(bundles=bundles)
        signed_bundles = client_two.sign(bundles=signed_bundles)
        user_one_flash = client_one.apply(signedBundles=signed_bundles)
        user_two_flash = client_two.apply(signedBundles=signed_bundles)

    ##########################################################
    # Step 9: Closing channel
    ##########################################################
    logger.info('############# Closing channel #############')
    closing_bundles = client_one.close()
    signed_bundles = client_one.sign(bundles=closing_bundles)
    signed_bundles = client_two.sign(bundles=signed_bundles)

    ##########################################################
    # Step 10: Finalizing channel
    ##########################################################
    # logger.info('############# Finalizing channel #############')
    # finalisation = client_one.finalize()  # attaches final bundle to Tangle

    logger.info('Done!')


if __name__ == '__main__':
    main()
