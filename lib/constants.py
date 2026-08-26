

HOST = "localhost"
TALLY_URL = f"http://{HOST}:"
TALLY_PORT = 9000

COMPANY_NAME = "abc"

envtype = "staging"

env_config = {
    "local": {
        "EVITAL_RX_HOST": "localhost",
        "EVITAL_RX_URL": f"http://localhost:4000/",
    },
    "staging": {
        "EVITAL_RX_HOST": "dev-api.evitalrx.in",
        "EVITAL_RX_URL": "https://ews-staging-api-product.portal-evital.com/",
    },
    "beta": {
        "EVITAL_RX_HOST": "beta-api.evitalrx.in",
        "EVITAL_RX_URL": "https://beta-api.evitalrx.in/",
    },
    "production": {
        "EVITAL_RX_HOST": "api.evitalrx.in",
        "EVITAL_RX_URL": "https://api.evitalrx.in/",
    },
}
EVITAL_RX_URL = env_config[envtype]["EVITAL_RX_URL"]
EVITAL_RX_HOST = env_config[envtype]["EVITAL_RX_HOST"]


EVITAL_RX_API_KEY = ""
ENCRYPTION_KEY = "kphEig0_Dtx3iq2-Ok19KP0MTtVnXxO0gMlJ4ggAzPE="

LOGIN_RESPONSE = {}
IS_LOGIN = False
RX_ACCOUNTS = []
TALLY_ACCOUNTS = []
TALLY_RESPONSE = []
COMPANY_MAPPING = []
MAPPING_TYPE = ""
ACCESS_TOKEN = ""
THREAD = None
STOP_THREAD = False
DISPLAY_SYNC_LOADER = False
REQUEST_TIMEOUT = 2000

MAPPING_HISTORY = {}
ONE_SYNC = []
LAST_SYNCED = ""
MOBILE = ""
MOBILE_VAR = None
CURRENT_BRANCH_SYNC = None
LAST_SYNC_VAR = None
REQUIRE_REBOOT = False
SYNC_TIMER = 0
CURRENT_BRANCH_SYNC_JSON = {}

VOUCHERS = {
    "company_data": {"list_of_companies": {}, "active_company": {}},
    "vouchers_data": {
        "payment_vouchers": {},
        "receipt_vouchers": {},
        "contra_vouchers": {},
        "journal_vouchers": {},
        "sales_vouchers": {},
        "purchase_vouchers": {},
    },
    "income_and_expenses_data": {
        "direct_incomes": {},
        "direct_expenses": {},
        "indirect_incomes": {},
        "indirect_expenses": {},
    },
    "assets_and_liabilities_data": {
        "fixed_assets": {},
        "current_assets": {},
        "current_liabilities": {},
        "loans": {},
        "loans_and_advances": {},
    },
    "report_data": {
        "balance_sheet": {},
        "profit_and_loss": {},
        "ratio_analysis": {},
        "trial_balance": {},
        "day_book": {},
        "stock_summary": {},
        "cash_flow": {},
        "fund_flow": {},
    },
    "other_data": {
        "sales_accounts": {},
        "purchase_accounts": {},
        "bank_accounts": {},
        "cash_in_hand": {},
        "sundry_debtors": {},
        "sundry_creditors": {},
        "capital_account": {},
        "reserves_and_surplus": {},
        "investments": {},
    },
}
IMPORTED_FIELDS = [
    "ledgers",
    "groups",
    "balance_sheet",
    "profit_and_loss",
    "ratio_analysis",
    # 'sales_accounts' ,
    # 'purchase_accounts' ,
    # 'bank_accounts' ,
    # 'cash_in_hand' ,
    # 'sundry_debtors' ,
    # 'sundry_creditors' ,
    # 'direct_incomes' ,
    # 'direct_expenses' ,
    # 'indirect_incomes' ,
    # 'indirect_expenses' ,
    # 'loans' ,
    # 'loans_and_advances' ,
    # 'fixed_assets' ,
    # 'current_assets' ,
    # 'current_liabilities' ,
    # 'capital_account' ,
    # 'reserves_and_surplus' ,
    # 'investments' ,
    # 'trial_balance' ,
    # 'stock_summary' ,
    # 'day_book' ,
    # 'cash_flow' ,
    # 'fund_flow' ,
    # 'payments_vouchers' ,
    # 'receipts_vouchers'
]

REQUEST_FORMATS = {
    #     "list_of_companies" : """<ENVELOPE>
    #     <HEADER>
    #         <VERSION>1</VERSION>
    #         <TALLYREQUEST>Export</TALLYREQUEST>
    #         <TYPE>Collection</TYPE>
    #         <ID>List of Companies</ID>
    #     </HEADER>
    #     <BODY>
    #         <DESC>
    #             <STATICVARIABLES />
    #             <TDL>
    #                 <TDLMESSAGE>
    #                     <COLLECTION ISMODIFY="No" ISFIXED="No" ISINITIALIZE="Yes" ISOPTION="No" ISINTERNAL="No" NAME="List of Companies">
    #                         <TYPE>Company</TYPE>
    #                         <NATIVEMETHOD>Name</NATIVEMETHOD>
    #                         <NATIVEMETHOD>StartingFrom</NATIVEMETHOD>
    #                     </COLLECTION>
    #                 </TDLMESSAGE>
    #             </TDL>
    #         </DESC>
    #     </BODY>
    # </ENVELOPE>
    #     """,
    "balance_sheet": """<ENVELOPE>
        <HEADER>
            <VERSION>1</VERSION>
            <REQVERSION>1</REQVERSION>
            <TALLYREQUEST>Export</TALLYREQUEST>
            <TYPE>DATA</TYPE>
            <ID>BALANCE SHEET</ID>
        </HEADER>
        <BODY>
            <DESC>
                <STATICVARIABLES>
                    <SVCURRENTCOMPANY>company_name</SVCURRENTCOMPANY>
                    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                    <EXPLODEFLAG>Yes</EXPLODEFLAG>
                    <SVFROMDATE>from_date</SVFROMDATE>
                    <SVTODATE>to_date</SVTODATE>
                </STATICVARIABLES>
            </DESC>
        </BODY>
    </ENVELOPE>
        """,
    "profit_and_loss": """<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <REQVERSION>1</REQVERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>DATA</TYPE>
        <ID>PROFIT AND LOSS</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVCURRENTCOMPANY>company_name</SVCURRENTCOMPANY>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                <EXPLODEFLAG>Yes</EXPLODEFLAG>
                <EXPLODEALLLEVELS>Yes</EXPLODEALLLEVELS>
                <SVFROMDATE>from_date</SVFROMDATE>
                <SVTODATE>to_date</SVTODATE>
            </STATICVARIABLES>
        </DESC>
    </BODY>
</ENVELOPE>
    """,
    "ratio_analysis": """<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>Ratio Analysis</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVCURRENTCOMPANY>company_name</SVCURRENTCOMPANY>
                <EXPLODEFLAG>Yes</EXPLODEFLAG>
                <EXPLODEALLLEVELS>Yes</EXPLODEALLLEVELS>
                <SVFROMDATE>from_date</SVFROMDATE>
                <SVTODATE>to_date</SVTODATE>
            </STATICVARIABLES>
        </DESC>
    </BODY>
</ENVELOPE>
    """,
    "list_of_companies": """<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>List of Companies</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES />
            <TDL>
                <TDLMESSAGE>
                    <COLLECTION ISMODIFY="No" ISFIXED="No" ISINITIALIZE="Yes" ISOPTION="No" ISINTERNAL="No" NAME="List of Companies">
                        <TYPE>Company</TYPE>
                        <NATIVEMETHOD>Name</NATIVEMETHOD>
                        <NATIVEMETHOD>GUID</NATIVEMETHOD>
                        <NATIVEMETHOD>StartingFrom</NATIVEMETHOD>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>""",
    "ledgers_data": """<ENVELOPE>
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
                <SVCURRENTCOMPANY>company_name</SVCURRENTCOMPANY>
                <SVFROMDATE>from_date</SVFROMDATE>
                <SVTODATE>to_date</SVTODATE>
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
</ENVELOPE>""",
    "groups_data": """<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <REQVERSION>1</REQVERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>GroupSummaries</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVCURRENTCOMPANY>company_name</SVCURRENTCOMPANY>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                <EXPLODEFLAG>Yes</EXPLODEFLAG>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <COLLECTION NAME="GroupSummaries" ISMODIFY="No" ISFIXED="No" ISINITIALIZE="No" ISOPTION="No" ISINTERNAL="No">
                        <TYPE>Group</TYPE>
                        <FETCH>NAME, PARENT, CLOSINGBALANCE, OPENINGBALANCE, CREDIT, DEBIT</FETCH>
                        <NATIVETYPE>Group</NATIVETYPE>
                        <CHILD OF="Group">
                            <FETCH>NAME, PARENT, CLOSINGBALANCE, OPENINGBALANCE</FETCH>
                        </CHILD>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>""",
}
SYNC_STAGE = 0
SYNC_BTN_TEXT = "Next"
LAST_SYNC_HEADER_VAR = ""
SYNC_START_DATE = ""
SYNC_END_DATE = ""

EXPORT_MODULES = {
    "Masters": ["Ledgers"],
    "Primary Vouchers": [
        "Sales",
        "Credit Note",
        "Purchase",
        "Debit Note",
        "Wholesale",
        "Wholesale Return",
    ],
    "Payment Vouchers": ["Receipt", "Payment", "Contra"],
}
SELECTED_MODULES = []

ROOT_WINDOW = None  # For thread-safe operations
ANIMATION_AFTER_ID = None
SHOW_LOG_WINDOW = False
LOAD_COMPLETE = False
