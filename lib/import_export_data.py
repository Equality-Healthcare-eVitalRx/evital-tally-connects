import io
import sys
from lib import constants
import requests
import xmltodict
import json
from tkinter import messagebox
import traceback
import logging
from log import LogManagerObj


def send_request_to_tally(request_params, request_format=""):
    headers = {"Content-Type": "application/xml"}
    try:
        response = requests.post(
            url=constants.TALLY_URL + str(constants.TALLY_PORT),
            data=request_params,
            headers=headers,
            timeout=constants.REQUEST_TIMEOUT,
        )
        response_content = response.content

        content = response_content.replace(b"&#4;", b"")
        if request_format == "profit_and_loss":
            content = content.replace(b"<BSNAME>", b"")
            content = content.replace(b"</BSNAME>", b"")
            content = content.replace(b"<BSAMT>", b"<PLAMT>")
            content = content.replace(b"</BSAMT>", b"</PLAMT>")
            content = content.replace(b"<BSSUBAMT>", b"<PLSUBAMT>")
            content = content.replace(b"</BSSUBAMT>", b"</PLSUBAMT>")

        def clean_data(data):
            if isinstance(data, dict):
                clean_dict = {}
                for key, value in data.items():
                    if key == "#type":  # Ignore #type
                        continue
                    elif key == "#text":  # Replace parent key's value with #text
                        return clean_data(value)
                    elif key.startswith("#"):  # Ignore other #attributes except #name
                        continue
                    else:
                        # Recursively clean nested dictionaries or lists
                        clean_dict[key] = clean_data(value)

                # Set default values for CLOSINGBALANCE and OPENINGBALANCE if they are missing or empty
                if "CLOSINGBALANCE" in clean_dict and not clean_dict["CLOSINGBALANCE"]:
                    clean_dict["CLOSINGBALANCE"] = "0"
                if "OPENINGBALANCE" in clean_dict and not clean_dict["OPENINGBALANCE"]:
                    clean_dict["OPENINGBALANCE"] = "0"

                return clean_dict
            elif isinstance(data, list):
                return [clean_data(item) for item in data]
            else:
                return data  # Return the value if it's not a dict or list

        if request_format in ["groups_data", "list_of_companies"]:
            raw_data = xmltodict.parse(content, attr_prefix="#")
            cleaned_data = clean_data(raw_data)

            # Convert the cleaned dictionary back to JSON
            output_json = json.dumps(cleaned_data)
            return output_json

        raw_data = xmltodict.parse(content)
        parsed_data = json.dumps(raw_data)

        # print("Data Fetched")
        return parsed_data

    except requests.exceptions.Timeout:
        LogManagerObj.write_log(traceback.format_exc())
        error_message = "Make sure tally is running."
        messagebox.showerror("Sync Failed", error_message)
    except requests.exceptions.RequestException as e:
        LogManagerObj.write_log(traceback.format_exc())
        error_message = str(e)
        error_message = "Make sure tally is running."
        messagebox.showerror("Sync Failed", error_message)
    return 0


def send_data_to_evitalrx(request_params):
    headers = {"Content-Type": "application/json"}
    res = {"status_code": 0, "status_message": "Error while importing data."}
    json_request = {
        "chemist_id": constants.LOGIN_RESPONSE["data"]["business_details"][
            "logged_in_business"
        ]["id"],
        "type": "fetch_data",
        "tally_data": request_params,
        "app_version": constants.APP_VERSION,
    }
    if constants.ACCESS_TOKEN != "":
        json_request["accesstoken"] = constants.ACCESS_TOKEN
    if constants.EVITAL_RX_API_KEY != "":
        json_request["apikey"] = constants.EVITAL_RX_API_KEY
    try:
        logging.info(
            constants.EVITAL_RX_URL
            + "v2/master/tally_data/v3/import_reports_data "
            + "API called"
        )
        response = requests.post(
            url=constants.EVITAL_RX_URL + "v2/master/tally_data/v3/import_reports_data",
            data=json.dumps(json_request),
            headers=headers,
            timeout=constants.REQUEST_TIMEOUT,
        )
        logging.info(
            constants.EVITAL_RX_URL
            + "v2/master/tally_data/v3/import_reports_data "
            + "API called - Status "
            + str(response.status_code)
        )
        logging.info(
            constants.EVITAL_RX_URL
            + "v2/master/tally_data/v3/import_reports_data "
            + "API called - Response "
            + str(response.content)
        )
        if response.status_code == 200:
            status = json.loads(response.content)
            return status
    except requests.exceptions.Timeout:
        LogManagerObj.write_log(traceback.format_exc())
        error_message = "Internet issue. Please try again later."
        # messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        error_message = "Internet issue. Please try again later."
        LogManagerObj.write_log(traceback.format_exc())
        # messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    return res


def send_login_request(mobile_no=None, password=None, entity="chemist", apikey=None):
    headers = {"Content-Type": "application/json"}
    if apikey:
        json_request = {
            "apikey": apikey,
            "login_entity": entity,
            "app_version": constants.APP_VERSION,
        }
    else:
        json_request = {
            "mobile": mobile_no,
            "password": password,
            "login_entity": entity,
            "app_version": constants.APP_VERSION,
        }
    response_dict = {"status_code": 0, "status_message": "Couldn't send request."}
    error_message = "Invalid mobile number or password."
    try:
        LogManagerObj.write_log(
            f"🔑 Request sent to {constants.EVITAL_RX_URL}"
        )
        # LogManagerObj.write_log(json.dumps(json_request))
        response = requests.post(
            url=constants.EVITAL_RX_URL + "v2/master/tally_data/v3/login",
            data=json.dumps(json_request),
            headers=headers,
            timeout=constants.REQUEST_TIMEOUT,
        )
        print(f"🔑 Login response status: {response.status_code}")
        print(f"🔑 Login response content: {response.content}")
        if response.status_code == 200:
            login_response = json.loads(response.content)
            if (
                login_response["status_code"] == "1"
                or login_response["status_code"] == 1
            ):
                constants.LOGIN_RESPONSE = login_response
                constants.RX_ACCOUNTS = list(
                    [
                        {
                            key: value
                            for key, value in login_response["data"][
                                "business_details"
                            ]["logged_in_business"].items()
                        }
                    ]
                )
                if constants.LOGIN_RESPONSE["data"]["business_details"][
                    "is_chain_business"
                ]:
                    if (
                        "child_businesses"
                        in login_response["data"]["business_details"].keys()
                        and login_response["data"]["business_details"][
                            "logged_in_business"
                        ]["is_HO"]
                    ):
                        constants.RX_ACCOUNTS += [
                            x
                            for x in login_response["data"]["business_details"][
                                "child_businesses"
                            ]
                        ]
                    if (
                        "HO_pharmacy"
                        in login_response["data"]["business_details"].keys()
                    ):
                        constants.RX_ACCOUNTS += list(
                            [
                                {
                                    key: value
                                    for key, value in login_response["data"][
                                        "business_details"
                                    ]["HO_pharmacy"].items()
                                }
                            ]
                        )

                return login_response
            error_message = login_response.get(
                "status_message", "Invalid mobile number or password."
            )
            messagebox.showerror("Login Failed", error_message)
        else:
            error_message = "Connection issue, Please try again."
            LogManagerObj.write_log(traceback.format_exc())
            messagebox.showerror("Login Failed", error_message)

    except requests.exceptions.Timeout:
        print(str(traceback.format_exc()))
        error_message = "Internet issue. Please try again later."
        LogManagerObj.write_log(traceback.format_exc())
        messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    except:
        print(str(traceback.format_exc()))
        # error_message = str(e)
        LogManagerObj.write_log(traceback.format_exc())
        error_message = "Internet issue. Please try again later."
        messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)

    return response_dict


def get_tally_companies():
    headers = {"Content-Type": "application/xml"}
    request_params = constants.REQUEST_FORMATS["list_of_companies"]
    # print(request_params)
    try:
        print(constants.TALLY_URL + str(constants.TALLY_PORT))
        response = requests.post(
            url=constants.TALLY_URL + str(constants.TALLY_PORT),
            data=request_params,
            headers=headers,
            timeout=3,
        )
        if response.status_code == 200:
            response_content = response.content
            content = response_content.replace(b"&#4;", b"")
            raw_data = xmltodict.parse(content)
            parsed_data = json.dumps(raw_data)
            parsed_data = json.loads(parsed_data)
            constants.TALLY_RESPONSE = parsed_data
            if (
                type(parsed_data["ENVELOPE"]["BODY"]["DATA"]["COLLECTION"]["COMPANY"])
                == list
            ):
                constants.TALLY_ACCOUNTS = [
                    {"company_name": x["@NAME"], "company_guid": x["GUID"]["#text"], "starting_from": x["STARTINGFROM"]["#text"]}
                    for x in parsed_data["ENVELOPE"]["BODY"]["DATA"]["COLLECTION"][
                        "COMPANY"
                    ]
                ]
            else:
                constants.TALLY_ACCOUNTS = [
                    {"company_name": x["@NAME"], "company_guid": x["GUID"]["#text"], "starting_from": x["STARTINGFROM"]["#text"]}
                    for x in [
                        parsed_data["ENVELOPE"]["BODY"]["DATA"]["COLLECTION"]["COMPANY"]
                    ]
                ]

        return parsed_data
    except requests.exceptions.Timeout:
        traceback.print_exc()
        LogManagerObj.write_log(traceback.format_exc())
        if constants.LOGIN_MODE == "apikey":
            # Debug session: keep the app usable even without Tally running.
            LogManagerObj.write_log("⚠ Debug mode: Tally connection timed out, continuing.")
            return 0
        error_message = "Connection timed out. Please try again later."
        messagebox.showerror("Tally Company", error_message)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        LogManagerObj.write_log(traceback.format_exc())
        if constants.LOGIN_MODE == "apikey":
            # Debug session: keep the app usable even without Tally running.
            LogManagerObj.write_log("⚠ Debug mode: Tally is not running, continuing.")
            return 0
        error_message = str(e)
        messagebox.showerror("Tally Company", "Tally is not running.")
        # import os

        # os.remove("./lib/app_cache.txt")
        sys.exit(1)
    except:
        LogManagerObj.write_log(traceback.format_exc())
        if constants.LOGIN_MODE == "apikey":
            # Debug session: keep the app usable even without Tally running.
            LogManagerObj.write_log("⚠ Debug mode: Tally is not running, continuing.")
            return 0
        messagebox.showerror("Tally Company", "Tally is not running.")
        # import os

        # os.remove("./lib/app_cache.txt")
        sys.exit(1)

    return 0


def map_rx_companies():
    headers = {"Content-Type": "application/json"}
    json_request = {
        "chemist_id": constants.LOGIN_RESPONSE["data"]["business_details"][
            "logged_in_business"
        ]["id"],
        "type": "map_companies",
        "companies_data": constants.COMPANY_MAPPING,
        "app_version": constants.APP_VERSION,
    }
    if constants.ACCESS_TOKEN != "":
        json_request["accesstoken"] = constants.ACCESS_TOKEN
    if constants.EVITAL_RX_API_KEY != "":
        json_request["apikey"] = constants.EVITAL_RX_API_KEY

    try:
        response = requests.post(
            url=constants.EVITAL_RX_URL + "v2/master/tally_data/v3/import_reports_data",
            data=json.dumps(json_request),
            headers=headers,
            timeout=constants.REQUEST_TIMEOUT,
        )
        return json.loads(response.content)
    except:
        LogManagerObj.write_log(traceback.format_exc())
        messagebox.showerror(
            "Map Companies", "Internet issues. Please try again later."
        )
    return 0


def remove_company_mapping(branch_apikey=""):
    headers = {"Content-Type": "application/json"}
    json_request = {
        "apikey": branch_apikey,
        "app_version": constants.APP_VERSION,
    }

    try:
        response = requests.post(
            url=constants.EVITAL_RX_URL + "v2/master/tally_data/v3/reset_application_mappings",
            data=json.dumps(json_request),
            headers=headers,
            timeout=constants.REQUEST_TIMEOUT,
        )
        return json.loads(response.content)
    except:
        LogManagerObj.write_log(traceback.format_exc())
        messagebox.showerror(
            "Remove Company Mapping", "Internet issues. Please try again later."
        )
    return 0


def reset_mapping_from_rx():
    headers = {"Content-Type": "application/json"}
    json_request = {
        "chemist_id": constants.LOGIN_RESPONSE["data"]["business_details"][
            "logged_in_business"
        ]["id"],
        "app_version": constants.APP_VERSION,
    }
    if constants.ACCESS_TOKEN != "":
        json_request["accesstoken"] = constants.ACCESS_TOKEN
    if constants.EVITAL_RX_API_KEY != "":
        json_request["apikey"] = constants.EVITAL_RX_API_KEY
    try:
        response = requests.post(
            url=constants.EVITAL_RX_URL
            + "v2/master/tally_data/v3/reset_application_mappings",
            data=json.dumps(json_request),
            headers=headers,
            timeout=constants.REQUEST_TIMEOUT,
        )
        messagebox.showinfo(
            "Mapping Reset", "Tally companies mapping reset successfully."
        )
        return json.loads(response.content)
    except:
        LogManagerObj.write_log(traceback.format_exc())
        messagebox.showerror(
            "Map Companies", "Internet issues. Please try again later."
        )
    return 0


def get_mapping_details():
    headers = {"Content-Type": "application/json"}
    json_request = {
        # "accesstoken" : constants.ACCESS_TOKEN,
        # "chemist_id" : constants.LOGIN_RESPONSE["data"]["business_details"]["logged_in_business"]["id"],
    }

    json_request["apikey"] = constants.EVITAL_RX_API_KEY
    json_request["app_version"] = constants.APP_VERSION
    if constants.EVITAL_RX_API_KEY == "":
        return {}
    try:
        response = requests.post(
            url=constants.EVITAL_RX_URL + "v2/master/tally_data/v3/get_mapping_details",
            data=json.dumps(json_request),
            headers=headers,
            timeout=constants.REQUEST_TIMEOUT,
        )
        response_josn = json.loads(response.content)
        if "data" in response_josn.keys():
            constants.MAPPING_HISTORY = (
                response_josn["data"]
                if isinstance(response_josn["data"], dict)
                else {}
            )

        return response_josn

    except:
        traceback.print_exc()
        LogManagerObj.write_log(traceback.format_exc())
        messagebox.showerror(
            "eVital<>Tally Connects", "Connection problem. Please try again later."
        )
        sys.exit(1)
    return 0


def get_last_synced_date():
    if (
        "last_synced_history" in constants.LOGIN_RESPONSE["data"].keys()
        and len(constants.LOGIN_RESPONSE["data"]["last_synced_date"]) > 0
    ):
        timestamps = [
            str(x["synced_timestamp"], "%Y-%m-%d H:M:S")
            for x in constants.LOGIN_RESPONSE["data"]["last_synced_date"]
        ]
        timestamps.sort()
        return timestamps[len(timestamps) - 1]


def is_tally_reachable(host=None, port=None):
    """Non-fatal connectivity check against Tally. Returns True/False."""
    try_host = constants.HOST if host is None else host
    try_port = constants.TALLY_PORT if port is None else port
    headers = {"Content-Type": "application/xml"}
    try:
        response = requests.post(
            url=f"http://{try_host}:{try_port}",
            data="",
            headers=headers,
            timeout=3,
        )
        return response.status_code == 200
    except Exception:
        LogManagerObj.write_log(traceback.format_exc())
        return False


def check_if_tally_running():
    headers = {"Content-Type": "application/xml"}
    try:
        response = requests.post(
            url=constants.TALLY_URL + str(constants.TALLY_PORT),
            data="",
            headers=headers,
            timeout=3,
        )
        response_content = response.content

        content = response_content.replace(b"&#4;", b"")
        raw_data = xmltodict.parse(content)
        parsed_data = json.dumps(raw_data)
        return True
    except:
        LogManagerObj.write_log(traceback.format_exc())
        messagebox.showerror("eVital<>Tally Connects", "Tally is not running")
        sys.exit(1)


def send_init_data_to_evital_rx(request_array, from_date, to_date):
    headers = {"Content-Type": "application/json"}
    res = {"status_code": 0, "status_message": "Error while importing data."}
    json_request = {
        # "accesstoken" : constants.ACCESS_TOKEN,
        # "start_date" : from_date,
        # "end_date" : to_date,
        # "groups_data" : "",
        # "ledgers_data" : "",
        "init_data": request_array,
        "app_version": constants.APP_VERSION,
        # "chemist_id" : constants.CHEMIST_ID
    }
    if constants.ACCESS_TOKEN != "":
        json_request["accesstoken"] = constants.ACCESS_TOKEN
    if constants.EVITAL_RX_API_KEY != "":
        json_request["apikey"] = constants.EVITAL_RX_API_KEY

    try:
        response = requests.post(
            url=constants.EVITAL_RX_URL
            + "v2/master/tally_data/v3/import_ledgers_and_groups",
            data=json.dumps(json_request),
            headers=headers,
            timeout=constants.REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            status = json.loads(response.content)
            return status
    except requests.exceptions.Timeout:
        LogManagerObj.write_log(traceback.format_exc())
        traceback.print_exc()
        error_message = "Internet issue. Please try again later."
    except requests.exceptions.RequestException as e:
        LogManagerObj.write_log(traceback.format_exc())
        traceback.print_exc()
        error_message = str(e)
        error_message = "Internet issue. Please try again later."

    return res


def get_data_from_evitalrx(start, end, api_key, type_, applicable_from_date=""):
    primary_mapping = {
        "Accounts": "accounts",
        "Sales": "sales",
        "Credit Note": "sales_return",
        "Purchase": "purchase",
        "Debit Note": "purchase_return",
        "Wholesale": "wholesale",
        "Wholesale Return": "wholesale_return",
        "Payment": "payment",
        "Receipt": "receipt",
        "Contra": "contra",
    }

    primary_mapping_val = primary_mapping.get(type_, "")
    type_ = str(type_).lower()
    url = constants.EVITAL_RX_URL + "/v2/master/reports/" + type_

    if type_ == "accounts":
        payload = {
            "apikey": api_key,
            "opening_balance_date": start,
            "applicable_from_date" : applicable_from_date,
            "is_tally": "true",
            "xml_import": "true",
            "app_version": constants.APP_VERSION,
        }
    elif primary_mapping_val in [
        "accounts",
        "sales",
        "sales_return",
        "purchase",
        "purchase_return",
        "wholesale",
        "wholesale_return",
    ]:
        url = constants.EVITAL_RX_URL + "/v2/master/reports/transactions"
        payload = {
            "apikey": api_key,
            "start_date": start,
            "end_date": end,
            "type": primary_mapping_val,
            "is_tally": "true",
            "xml_import": "true",
            "app_version": constants.APP_VERSION,
        }
    elif type_ in ["payment", "receipt", "contra"]:
        payload = {
            "apikey": api_key,
            "start_date": start,
            "end_date": end,
            "is_tally": "true",
            "xml_import": "true",
            "app_version": constants.APP_VERSION,
        }

    if constants.LOGIN_MODE == "apikey":
        # Debug session - don't store this request in the entity's
        # API request log.
        payload["store_api_request_log"] = "no"

    try:
        response = requests.post(
            url=url, data=payload, timeout=constants.REQUEST_TIMEOUT
        )
    except Exception as e:
        print(type_)
        traceback.print_exc()
        LogManagerObj.write_log(traceback.format_exc())
        return {"error": str(e)}
    if response.status_code == 200:
        return {api_key: response.json()}
    else:
        LogManagerObj.write_log(traceback.format_exc())
        return {"error": f"Status code {response.status_code}"}


def get_entity_sync_history(date_range="last_7_days", page=1, rpp=20):
    res = {"status_code": 0, "status_message": "Couldn't fetch sync history."}
    if constants.EVITAL_RX_API_KEY == "":
        res["status_message"] = "No API key found. Please login again."
        return res
    url = constants.EVITAL_RX_URL + "v2/master/reports/get_entity_sync_history"
    payload = {
        "apikey": constants.EVITAL_RX_API_KEY,
        "date_range": date_range,
        "rpp": str(rpp),
        "page": str(page),
        "app_version": constants.APP_VERSION,
    }
    try:
        logging.info(url + " API called")
        response = requests.post(
            url,
            files={k: (None, v) for k, v in payload.items()},
            timeout=300,
        )
        logging.info(url + f" API called - Status {response.status_code}")
        if response.status_code == 200:
            api_res = json.loads(response.content)
            if isinstance(api_res, dict):
                if "data" in api_res and isinstance(api_res["data"], dict):
                    data = api_res["data"]
                    data.setdefault("results", data.get("results", []))
                    data.setdefault("total_records", data.get("total_records", len(data["results"])))
                    data.setdefault("rpp", rpp)
                    data.setdefault("page", page)
                else:
                    api_res.setdefault("status_code", "1")
                    api_res.setdefault("data", {})
                    api_res["data"].setdefault("results", api_res.get("results", []))
                    api_res["data"].setdefault("total_records", api_res.get("total_records", len(api_res["data"]["results"])))
                    api_res["data"].setdefault("rpp", rpp)
                    api_res["data"].setdefault("page", page)
            return api_res
        res["status_message"] = f"🚨 API Error: {response.text}"
    except requests.exceptions.Timeout:
        LogManagerObj.write_log(traceback.format_exc())
        res["status_message"] = "Internet issue. Please try again later."
    except Exception:
        LogManagerObj.write_log(traceback.format_exc())
        res["status_message"] = "Internet issue. Please try again later."
    return res


def send_reconciliation(
    file_content: str, start_date: str, end_date: str, api_keys=[]
) -> dict:
    def build_payload(api_key):
        return {
            "apikey": api_key,
            "start_date": start_date,
            "end_date": end_date,
            "app_version": constants.APP_VERSION,
        }

    results = {}

    for api_key in api_keys:
        print(f"\n🔑 Reconciliation for API key: {api_key}")

        url = constants.EVITAL_RX_URL + "/v2/master/reports/reconciliation"
        # print("file_content:", file_content)
        try:
            # 🔴 IN-MEMORY FILE (no disk)
            file_obj = io.BytesIO(file_content.encode("utf-8"))
            with open("./lib/tally_recon.txt", "w") as f:
                f.write(file_content)

            files = {"file": ("tally_recon.txt", file_obj, "text/plain")}

            data = build_payload(api_key)

            res = requests.post(url, data=data, files=files)

            if res.status_code != 200:
                raise Exception(res.text)

            results[api_key] = res.json()
            print(f"✅ Reconciliation success for {api_key}")

        except Exception as e:
            print(f"❌ Reconciliation failed for {api_key}: {e}")
            results[api_key] = {"error": str(e)}

    return results
