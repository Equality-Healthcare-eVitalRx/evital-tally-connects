import requests

from lib import constants


class APIClient:
    def __init__(self):
        self.api_keys = API_KEYS  # list of keys

    def post(self, endpoint: str, data: dict):
        url = f"{BASE_URL}/{endpoint}"

        print("\n➡️ API CALL:", url)

        try:
            response = requests.post(url, data=data)
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

        print("📡 STATUS:", response.status_code)
        print("📡 RESPONSE DATA:", response)

        if response.status_code != 200:
            raise Exception(f"🚨 API Error: {response.text}")

        try:
            return response.json()
        except Exception:
            raise Exception(f"Invalid JSON response: {response.text}")

    # ========================
    # MULTI-KEY SYNC HELPER
    # ========================

    def _sync_all_keys(self, endpoint: str, build_payload: callable) -> dict[str, any]:
        """
        Loops over all configured API keys and calls the given endpoint for each.

        Args:
            endpoint:      The API endpoint name (e.g. "accounts").
            build_payload: A callable that accepts an api_key and returns the
                           payload dict to POST (excluding the apikey field).

        Returns:
            A dict keyed by api_key, each value being the API response for that key.
            Failed keys are stored as {"error": "<message>"}.
        """
        results = {}

        for api_key in self.api_keys:
            print(f"\n🔑 Syncing with API key: {api_key}")
            payload = build_payload(api_key)
            try:
                results[api_key] = self.post(endpoint, payload)
                print(f"✅ Success for key: {api_key}")
            except Exception as e:
                print(f"❌ Failed for key {api_key}: {e}")
                results[api_key] = {"error": str(e)}

        return results

    # ========================
    # ENDPOINT METHODS
    # ========================

    def fetch_accounts(self, opening_balance_date) -> dict:
        return self._sync_all_keys(
            endpoint="accounts",
            build_payload=lambda key: {
                "apikey": key,
                "opening_balance_date": opening_balance_date,
                "is_tally": "true",
                "xml_import": "true",
                "app_version": constants.APP_VERSION,
            },
        )

    def fetch_transactions(self, start, end, type_) -> dict:
        return self._sync_all_keys(
            endpoint="transactions",
            build_payload=lambda key: {
                "apikey": key,
                "start_date": start,
                "end_date": end,
                "type": type_,
                "is_tally": "true",
                "xml_import": "true",
                "app_version": constants.APP_VERSION,
            },
        )

    def fetch_payment(self, start, end) -> dict:
        return self._sync_all_keys(
            endpoint="payment",
            build_payload=lambda key: {
                "apikey": key,
                "start_date": start,
                "end_date": end,
                "is_tally": "true",
                "xml_import": "true",
                "app_version": constants.APP_VERSION,
            },
        )

    def fetch_receipt(self, start, end) -> dict:
        return self._sync_all_keys(
            endpoint="receipt",
            build_payload=lambda key: {
                "apikey": key,
                "start_date": start,
                "end_date": end,
                "is_tally": "true",
                "xml_import": "true",
                "app_version": constants.APP_VERSION,
            },
        )

    def fetch_contra(self, start, end) -> dict:
        return self._sync_all_keys(
            endpoint="contra",
            build_payload=lambda key: {
                "apikey": key,
                "start_date": start,
                "end_date": end,
                "is_tally": "true",
                "xml_import": "true",
            },
        )
