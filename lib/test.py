
# import xmltodict


# file_dir = "C:\\Users\\Evita\\Downloads\\Untitled (10)"

# with open(file_dir, "r" ) as file:
#     # print(file.read())
#     data = xmltodict.parse(file.read().encode('utf-8'))
    
    
import requests
request_params = """<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>EXPORT</TALLYREQUEST>
        <TYPE>DATA</TYPE>
        <ID>CA_LEDGER</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                <SVCURRENTCOMPANY>EvitalRx Smit</SVCURRENTCOMPANY>
                <SVFROMDATE>20230401</SVFROMDATE>
                <SVTODATE>20240331</SVTODATE>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <REPORT ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO"ISINTERNAL="NO" NAME="CA_LEDGER">
                        <FORM>CA_LEDGER</FORM>
                    </REPORT>
                    <FORM ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO" ISINTERNAL="NO"NAME="CA_LEDGER">
                        <PART>CA_LEDGER</PART>
                        <XMLTAG>LEDGERS</XMLTAG>
                    </FORM>
                    <PART ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO" ISINTERNAL="NO"NAME="CA_LEDGER">
                        <LINE>CA_LEDGER</LINE>
                        <REPEAT>CA_LEDGER:CA_LEDGERCOLLECTION</REPEAT>
                        <SCROLLED>Vertical</SCROLLED>
                    </PART>
                    <LINE ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO" ISINTERNAL="NO"NAME="CA_LEDGER">
                        <FIELDS>CA_NAME,CA_PARENT,CA_OPENINGBALANCE,CA_CLOSINGBALANCE</FIELDS>
                        <XMLTAG>LEDGER</XMLTAG>
                    </LINE>
                    <FIELD ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO"ISINTERNAL="NO" NAME="CA_NAME">
                        <SET>$NAME</SET>
                        <XMLTAG>NAME</XMLTAG>
                    </FIELD>
                    <FIELD ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO"ISINTERNAL="NO" NAME="CA_PARENT">
                        <SET>$PARENT</SET>
                        <XMLTAG>PARENT</XMLTAG>
                    </FIELD>
                    <FIELD ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO"ISINTERNAL="NO" NAME="CA_OPENINGBALANCE">
                        <TYPE>Amount</TYPE>
                        <SET>$OPENINGBALANCE</SET>
                        <XMLTAG>OPENINGBALANCE</XMLTAG>
                    </FIELD>
                    <FIELD ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO"ISINTERNAL="NO" NAME="CA_CLOSINGBALANCE">
                        <TYPE>Amount</TYPE>
                        <SET>$CLOSINGBALANCE</SET>
                        <XMLTAG>CLOSINGBALANCE</XMLTAG>
                    </FIELD>
                    <COLLECTION ISMODIFY="NO" ISFIXED="NO" ISINITIALIZE="NO" ISOPTION="NO"ISINTERNAL="NO" NAME="CA_LEDGERCOLLECTION">
                        <TYPE>Ledger</TYPE>
                        <NATIVEMETHOD>Name</NATIVEMETHOD>
                        <NATIVEMETHOD>Parent</NATIVEMETHOD>
                        <NATIVEMETHOD>OpeningBalance</NATIVEMETHOD>
                        <NATIVEMETHOD>ClosingBalance</NATIVEMETHOD>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>"""

headers = {'Content-Type': 'application/xml'}
response = requests.post(url="http://localhost:9000", data=request_params, headers=headers, timeout=5)
response_content = response.content

content = response_content.replace(b'&#4;', b'')

# print(content)
import re
# content = re.sub(r'\s*type\s*=\s*["\'][^"\']*["\']', '', content.decode('utf-8'), flags=re.IGNORECASE)
# content = content.encode('utf-8')
print('➡ lib/test.py:55 content:', content)

import xmltodict
import json

raw_data = xmltodict.parse(content, attr_prefix='#')
parsed_data = json.dumps(raw_data) 
print('➡ lib/test.py:125 parsed_data:', parsed_data)

# parsed_data = raw_data 
# print('➡ lib/test.py:61 parsed_data:', parsed_data)

# def clean_data(data):
#     if isinstance(data, dict):
#         clean_dict = {}
#         for key, value in data.items():
#             if key == "#type":  # Ignore #type
#                 continue
#             elif key == "#text":  # Replace parent key's value with #text
#                 return clean_data(value)
#             elif key.startswith("#"):  # Ignore other #attributes except #name
#                 continue
#             else:
#                 # Recursively clean nested dictionaries or lists
#                 clean_dict[key] = clean_data(value)
        
#         # Set default values for CLOSINGBALANCE and OPENINGBALANCE if they are missing or empty
#         if "CLOSINGBALANCE" in clean_dict and not clean_dict["CLOSINGBALANCE"]:
#             clean_dict["CLOSINGBALANCE"] = "0"
#         if "OPENINGBALANCE" in clean_dict and not clean_dict["OPENINGBALANCE"]:
#             clean_dict["OPENINGBALANCE"] = "0"
        
#         return clean_dict
#     elif isinstance(data, list):
#         return [clean_data(item) for item in data]
#     else:
#         return data  # Return the value if it's not a dict or list

# # Clean the parsed data
# cleaned_data = clean_data(parsed_data)

# # Convert the cleaned dictionary back to JSON
# output_json = json.dumps(cleaned_data, indent=4)

# # Print the cleaned JSON
# print(output_json)
# with open("C:\\comp\\local\\Softwares\\py-extract-tally\\data.json", "w") as file:    
#     json.dump(cleaned_data,file)

 
import xml.etree.ElementTree as ET
import json

# XML data as a string
# xml_data = """
# <root>
#     <item>
#         <name>Item 1</name>
#         <price>10.50</price>
#     </item>
#     <item>
#         <name>Item 2</name>
#         <price>20.75</price>
#     </item>
# </root>
# """

# # Parse the XML
# root = ET.fromstring(content)

# # Function to convert XML to dictionary
# def xml_to_dict(element):
#     result = {}
#     for child in element:
#         if len(child):
#             result[child.tag] = xml_to_dict(child)
#         else:
#             result[child.tag] = child.text
#     return result

# # Convert the entire XML tree
# dict_data = {root.tag: [xml_to_dict(item) for item in root]}

# # Convert dictionary to JSON
# json_data = json.dumps(dict_data, indent=4)

# print(json_data)
