import sys
from lib import constants
import requests
import xmltodict
import json
import re
from tkinter import messagebox
from datetime import datetime
import traceback
import logging

def send_request_to_tally(request_params, request_format = ""):
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(url=constants.TALLY_URL+str(constants.TALLY_PORT), data=request_params, headers=headers, timeout=constants.REQUEST_TIMEOUT)
        response_content = response.content
        
        # logging.info("Tally Data Fetched")
        # l("Tally Data Fetched")
        content = response_content.replace(b'&#4;', b'')
        if request_format == "profit_and_loss":
            content = content.replace(b'<BSNAME>', b'')
            content = content.replace(b'</BSNAME>', b'')
            content = content.replace(b'<BSAMT>', b'<PLAMT>')
            content = content.replace(b'</BSAMT>', b'</PLAMT>')
            content = content.replace(b'<BSSUBAMT>', b'<PLSUBAMT>')
            content = content.replace(b'</BSSUBAMT>', b'</PLSUBAMT>')
            # print('➡ lib/import_export_data.py:25 content:', content)
                
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
            
        if request_format in ["groups_data","list_of_companies"]:
            
            raw_data = xmltodict.parse(content, attr_prefix='#')
            cleaned_data = clean_data(raw_data)

            # Convert the cleaned dictionary back to JSON
            output_json = json.dumps(cleaned_data)
            return output_json
            
        raw_data = xmltodict.parse(content)
        parsed_data = json.dumps(raw_data) 

        #print("Data Fetched")
        return parsed_data
    
    except requests.exceptions.Timeout:
        # logging.error("API timeout - send_request_to_tally")
        error_message = "Make sure tally is running."
        messagebox.showerror("Sync Failed", error_message)
        # save_error_message(error_message)
    except requests.exceptions.RequestException as e:
        # logging.error("Tally Exception - "+str(e))
        error_message = str(e)
        error_message = "Make sure tally is running."
        messagebox.showerror("Sync Failed", error_message)
    return 0

def send_data_to_evitalrx(request_params):
    headers = {'Content-Type': 'application/json'}
    res = {
        "status_code" : 0,
        "status_message" : "Error while importing data."
    }
    # #print('➡ lib/import_export_data.py:36 constants.LOGIN_RESPONSE:', constants.LOGIN_RESPONSE)
    json_request = {
        # "accesstoken" : constants.ACCESS_TOKEN,
        "chemist_id" : constants.LOGIN_RESPONSE["data"]["business_details"]["logged_in_business"]["id"],
        "type" : "fetch_data",
        "tally_data" : request_params,
        # "chemist_id" : constants.CHEMIST_ID
    }
    #print('➡ lib/import_export_data.py:44 json_request:', json_request)
    if constants.ACCESS_TOKEN != "":
        json_request["accesstoken"] = constants.ACCESS_TOKEN
    if constants.EVITAL_RX_API_KEY != "":
        json_request["apikey"] = constants.EVITAL_RX_API_KEY
    # #print('➡ lib/import_export_data.py:27 json_request:', json_request)
    #print(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_reports_data")
    try:
        #print('➡ lib/import_export_data.py:27 response:', response)
        logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v3/import_reports_data " + "API called")
        response = requests.post(url=constants.EVITAL_RX_URL+"v2/master/tally_data/v3/import_reports_data", data=json.dumps(json_request), headers=headers, timeout=constants.REQUEST_TIMEOUT)
        logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v3/import_reports_data " + "API called - Status "+str(response.status_code))
        logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v3/import_reports_data " + "API called - Response "+str(response.content))
        if response.status_code == 200:
            #print(response.content)
            status = json.loads(response.content)
            # res = status
            # if status["status_code"] not in [1,'1']:
            #     messagebox.showerror("Sync Failed", status["status_message"])
                #print("complete")
            return status
    except requests.exceptions.Timeout:
        error_message = "Internet issue. Please try again later."
        # messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        error_message = "Internet issue. Please try again later."
        # messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    return res

def send_login_request(mobile_no, password, entity="chemist"):
    headers = {'Content-Type': 'application/json'}
    json_request = {
        "mobile" : mobile_no,
        "password" : password,
        "login_entity" : entity
    }
    print('➡ lib/import_export_data.py:136 json_request:', json_request)
    response_dict = {
        "status_code" : 0,
        "status_message" : "Couldn't send request."
    }
    try:
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/tally_app/login " + "API called ")
        response = requests.post(url=constants.EVITAL_RX_URL+"v2/master/tally_data/v3/login", data=json.dumps(json_request), headers=headers, timeout=constants.REQUEST_TIMEOUT)
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/tally_app/login " + "API called - Status "+str(response.status_code))
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/tally_app/login " + "API called - Response "+str(response.content))
        print('➡ lib/import_export_data.py:78 response:', response)
        if response.status_code == 200:
            login_response = json.loads(response.content)
            if login_response["status_code"] == "1" or login_response["status_code"] == 1:
                constants.LOGIN_RESPONSE = login_response
                #print(login_response["data"]["business_details"]["logged_in_business"])
                constants.RX_ACCOUNTS = list([{key:value for key,value in login_response["data"]["business_details"]["logged_in_business"].items()}])
                if constants.LOGIN_RESPONSE["data"]["business_details"]["is_chain_business"]:
                    if "child_businesses" in login_response["data"]["business_details"].keys() and login_response["data"]["business_details"]["logged_in_business"]["is_HO"]:
                        constants.RX_ACCOUNTS += [x for x in login_response["data"]["business_details"]["child_businesses"]]
                    if "HO_pharmacy" in login_response["data"]["business_details"].keys():
                        constants.RX_ACCOUNTS += list([{key:value for key,value in login_response["data"]["business_details"]["HO_pharmacy"].items()}])
                  
                
                #print('➡ lib/import_export_data.py:56 RX_ACCOUNTS:', constants.RX_ACCOUNTS)
                #print('➡ lib/import_export_data.py:55 LOGIN_RESPONSE:', constants.LOGIN_RESPONSE)
                return login_response
            error_message = "Invalid mobile number or password."
            messagebox.showerror("Login Failed", error_message)
        else:
            error_message = "Connection issue, Please try again."
            messagebox.showerror("Login Failed", error_message)
            # return response_dict
            # return response_dict
            
    except requests.exceptions.Timeout:
        print(str(traceback.format_exc()))
        error_message = "Internet issue. Please try again later."
        messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    except:
        print(str(traceback.format_exc()))
        # error_message = str(e)
        error_message = "Internet issue. Please try again later."
        messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    
    return response_dict

def get_tally_companies():
    headers = {'Content-Type': 'application/xml'}
    request_params = constants.REQUEST_FORMATS["list_of_companies"]
    
    try:
        
        # logging.info(constants.TALLY_URL+"/get_tally_companies " + "API called  ")
        response = requests.post(url=constants.TALLY_URL+str(constants.TALLY_PORT), data=request_params, headers=headers, timeout=3)
        # logging.info(constants.TALLY_URL+"/get_tally_companies " + "API called - Status "+str(response.status_code))
        # logging.info(constants.EVITAL_RX_URL+"get_tally_companies " + "API called - Response "+str(response.content))
        if response.status_code == 200:
            response_content = response.content
            content = response_content.replace(b'&#4;', b'')
            raw_data = xmltodict.parse(content)
            parsed_data = json.dumps(raw_data) 
            parsed_data = json.loads(parsed_data)
            constants.TALLY_RESPONSE = parsed_data
            #print('➡ lib/import_export_data.py:75 TALLY_RESPONSE:', constants.TALLY_RESPONSE)
            if type(parsed_data["ENVELOPE"]["BODY"]["DATA"]["COLLECTION"]["COMPANY"]) == list:
                constants.TALLY_ACCOUNTS = [{"company_name":x["@NAME"],"company_guid":x["GUID"]["#text"]} for x in parsed_data["ENVELOPE"]["BODY"]["DATA"]["COLLECTION"]["COMPANY"]]
            else:
                constants.TALLY_ACCOUNTS = [{"company_name":x["@NAME"],"company_guid":x["GUID"]["#text"]} for x in [parsed_data["ENVELOPE"]["BODY"]["DATA"]["COLLECTION"]["COMPANY"]]]
            
        #print('➡ lib/import_export_data.py:72 TALLY_ACCOUNTS:', constants.TALLY_ACCOUNTS)
    
    # #print('➡ lib/import_export_data.py:70 parsed_data:', parsed_data)
        #print("Data Fetched")
        return parsed_data
    except requests.exceptions.Timeout:
        error_message = "Connection timed out. Please try again later."
        messagebox.showerror("Tally Company", error_message)
        # logging.error(error_message)
        sys.exit(1)
        # save_error_message(error_message)
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        messagebox.showerror("Tally Company", "Tally is not running.")
        # logging.error("Tally not running")
        sys.exit(1)
    except:
        messagebox.showerror("Tally Company", "Tally is not running.")
        # logging.error("Tally not running")
        sys.exit(1)
        # save_error_message(error_message)

    return 0

def map_rx_companies():
    headers = {'Content-Type': 'application/json'}
    # #print(constants.LOGIN_RESPONSE)
    json_request = {
        # "accesstoken" : constants.ACCESS_TOKEN,
        "chemist_id" : constants.LOGIN_RESPONSE["data"]["business_details"]["logged_in_business"]["id"],
        "type" : "map_companies",
        "companies_data" : constants.COMPANY_MAPPING,
    }
    if constants.ACCESS_TOKEN != "":
        json_request["accesstoken"] = constants.ACCESS_TOKEN
    if constants.EVITAL_RX_API_KEY != "":
        json_request["apikey"] = constants.EVITAL_RX_API_KEY
    print('➡ lib/import_export_data.py:145 json_request:', json_request)
    # if len(constants.COMPANY_MAPPING)>0:
         
    try:
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_reports_data " + "API called ")
        response = requests.post(url=constants.EVITAL_RX_URL+"v2/master/tally_data/v3/import_reports_data", data=json.dumps(json_request), headers=headers, timeout=constants.REQUEST_TIMEOUT)
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_reports_data " + "API called - Status "+str(response.status_code))
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_reports_data " + "API called - Response "+str(response.content))
        print('➡ lib/import_export_data.py:149 response:', response.content)
        # messagebox.showinfo("Company Mapping", "Comapny mapped successfully.")
        return json.loads(response.content)
    except:
        messagebox.showerror("Map Companies","Internet issues. Please try again later.")
        # logging.error("Internet issues. Please try again later.")
    return 0
    
def reset_mapping_from_rx():
    headers = {'Content-Type': 'application/json'}
    json_request = {
        # "accesstoken" : constants.ACCESS_TOKEN,
        "chemist_id" : constants.LOGIN_RESPONSE["data"]["business_details"]["logged_in_business"]["id"],
    }
    if constants.ACCESS_TOKEN != "":
        json_request["accesstoken"] = constants.ACCESS_TOKEN
    if constants.EVITAL_RX_API_KEY != "":
        json_request["apikey"] = constants.EVITAL_RX_API_KEY
    try:
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/reset_application_mappings " + "API called  ")
        response = requests.post(url=constants.EVITAL_RX_URL+"v2/master/tally_data/v3/reset_application_mappings", data=json.dumps(json_request), headers=headers, timeout=constants.REQUEST_TIMEOUT)
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/reset_application_mappings " + "API called - Status "+str(response.status_code))
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/reset_application_mappings " + "API called - Response "+str(response.content))
        #print('➡ lib/import_export_data.py:149 response:', response.content)
        messagebox.showinfo("Mapping Reset","Tally companies mapping reset successfully.")
        return json.loads(response.content)
    except:
        messagebox.showerror("Map Companies","Internet issues. Please try again later.")
        # logging.error("Internet issues. Please try again later.")
    return 0

def get_mapping_details():
    headers = {'Content-Type': 'application/json'}
    json_request = {
        # "accesstoken" : constants.ACCESS_TOKEN,
        # "chemist_id" : constants.LOGIN_RESPONSE["data"]["business_details"]["logged_in_business"]["id"],
    }
    # if constants.ACCESS_TOKEN != "":
    #     json_request["accesstoken"] = constants.ACCESS_TOKEN
    # if constants.EVITAL_RX_API_KEY != "":
    
    # json_data = json.load(open("./lib/app_cache.txt", "rb"))
    # json_data["login_response"]["data"]
   
       
    json_request["apikey"] = constants.EVITAL_RX_API_KEY
    if constants.EVITAL_RX_API_KEY == "":
        print("blank api key")
        return {}
    # print('➡ lib/import_export_data.py:265 json_request:', json_request)
    # if constants.EVITAL_RX_API_KEY == "":
    #     return {}
    try:
        logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v3/get_mapping_details " + "API called ")
        response = requests.post(url=constants.EVITAL_RX_URL+"v2/master/tally_data/v3/get_mapping_details", data=json.dumps(json_request), headers=headers, timeout=constants.REQUEST_TIMEOUT)
        logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v3/get_mapping_details " + "API called - Status "+str(response.status_code))
        logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v3/get_mapping_details " + "API called - Response "+str(response.content))
        #print('➡ lib/import_export_data.py:149 response:', response.content)
        
        response_josn = json.loads(response.content)
        # print('➡ lib/import_export_data.py:284 response_josn:', response_josn)
        # print('➡ lib/import_export_data.py:284 response_josn:', type(response_josn))
#         response_josn = {
#     "status_code": "1",
#     "status_message": "Tally Company mappings fetched successfully",
#     "datetime": "2025-01-04 17:39:07",
#     "data": {
#         "login_entity_last_synced": "",
#         "results": [
#             {
#                 "chemist_id": "rM9k/ftzTZOC2y9KFKF5Vg==",
#                 "evitalrx_branch_name": "Smit Pharmacy, Ahmedabad",
#                 "tally_company_name": "Smit Pharmacy",
#                 "last_synced": "25 min ago",
#                 "is_mapped": "false"
#             },
#             {
#                 "chemist_id": "4rCzgqEKT1jjLrpV/6xShg==",
#                 "evitalrx_branch_name": "Shyam Pharmacy, Ahmedabad",
#                 "tally_company_name": "",
#                 "last_synced": "",
#                 "is_mapped": "true"
#             }
#         ]
#     }
# }
        if "data" in response_josn.keys():
            constants.MAPPING_HISTORY = response_josn["data"]
            
            
        # messagebox.showinfo("Mapping Reset","Tally companies mapping reset successfully.")
        # print('➡ lib/import_export_data.py:284 response_josn:', response_josn)
        return json.loads(response.content)
    
    except:
        messagebox.showerror("Tally Sync","Connection problem. Please try again later.")
        # logging.error("Connection problem. Please try again later.")
        sys.exit(1)
    return 0

def get_last_synced_date():
    if "last_synced_history" in constants.LOGIN_RESPONSE["data"].keys() and len(constants.LOGIN_RESPONSE["data"]["last_synced_date"]) > 0 :
        timestamps = [str(x['synced_timestamp'], "%Y-%m-%d H:M:S") for x in constants.LOGIN_RESPONSE["data"]["last_synced_date"]]
        # timestamps 
        timestamps.sort()
        return timestamps[len(timestamps)-1]
    
    
def check_if_tally_running():
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(url=constants.TALLY_URL+str(constants.TALLY_PORT), data="", headers=headers, timeout=3)
        print('➡ lib/import_export_data.py:271 response:', response)
        response_content = response.content
        # logging.info(constants.EVITAL_RX_URL+"check_if_tally_running " + "API called - Status "+str(response.status_code))
        
        content = response_content.replace(b'&#4;', b'')
        raw_data = xmltodict.parse(content)
        parsed_data = json.dumps(raw_data) 
        print('➡ lib/import_export_data.py:199 parsed_data:', parsed_data)
        #print("Data Fetched")
        return True
    except:
        # print(str(traceback.format_exc()))
        messagebox.showerror("Tally Sync", "Tally is not running")
        sys.exit(1)
        # return False
    
def send_init_data_to_evital_rx(request_array, from_date, to_date):
    # #print('➡ lib/import_export_data.py:225 request_array:', request_array)
    headers = {'Content-Type': 'application/json'}
    res = {
        "status_code" : 0,
        "status_message" : "Error while importing data."
    }
    # #print('➡ lib/import_export_data.py:36 constants.LOGIN_RESPONSE:', constants.LOGIN_RESPONSE)
    json_request = {
        # "accesstoken" : constants.ACCESS_TOKEN,
        # "start_date" : from_date,
        # "end_date" : to_date,
        # "groups_data" : "",
        # "ledgers_data" : "",
        "init_data" : request_array
        # "chemist_id" : constants.CHEMIST_ID
    }
    #print('➡ lib/import_export_data.py:239 json_request:', json_request)
    if constants.ACCESS_TOKEN != "":
        json_request["accesstoken"] = constants.ACCESS_TOKEN
    if constants.EVITAL_RX_API_KEY != "":
        json_request["apikey"] = constants.EVITAL_RX_API_KEY
    # #print('➡ lib/import_export_data.py:27 json_request:', json_request)
    #print(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_ledgers_and_groups")
    # for single_request in request_array:
    #     json_request["groups_data"] = single_request["groups_data"]
    #     json_request["ledgers_data"] = single_request["ledgers_data"]
    #     #print('➡ lib/import_export_data.py:250 json_request:', json_request)
        # with open("./lib/data2.json", "w") as json_file:
        #     json.dump(json_request, json_file)
    try:
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_ledgers_and_groups " + "API called - ")
        response = requests.post(url=constants.EVITAL_RX_URL+"v2/master/tally_data/v3/import_ledgers_and_groups", data=json.dumps(json_request), headers=headers, timeout=constants.REQUEST_TIMEOUT)
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_ledgers_and_groups " + "API called - Status "+str(response.status_code))
        # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_ledgers_and_groups " + "API called - Response "+str(response.content))
        #print('➡ lib/import_export_data.py:27 response:', response)
        if response.status_code == 200:
            # logging.info(constants.EVITAL_RX_URL+"v2/master/tally_data/v2/import_ledgers_and_groups " + "API called - Status "+str(response.status_code))
            # json.dumps()
            # #print(response.content)
            status = json.loads(response.content)
            # if status["status_code"] not in [1,'1']:
            #     messagebox.showerror("Sync Failed", status["status_message"])
                #print("complete")
            return status
    except requests.exceptions.Timeout:
        error_message = "Internet issue. Please try again later."
        # logging.error("Internet issue. Please try again later. ")
        # messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        error_message = "Internet issue. Please try again later."
        # logging.error("Internet issue. Please try again later. ")
        # messagebox.showerror("Login Failed", error_message)
        # save_error_message(error_message)
    return res