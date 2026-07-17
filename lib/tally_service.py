import requests
import time
import re
import html
from lib import constants
from log import LogManagerObj


class TallyService:
    def clean_xml(self, xml):
        if not xml:
            return ""
        return (
            xml.strip()
            .replace("\\n", "")
            .replace("\n", "")
            .replace("\t", "")
            .replace("\xa0", " ")
        )

    def build_envelope(
        self, messages, report_name="Vouchers", company_name="$$CurrentCompany"
    ):
        combined = "\n".join([self.clean_xml(m) for m in messages])
        return f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>{report_name}</REPORTNAME>
        <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>{combined}</REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>"""

    def push_batch(
        self,
        xml_list,
        report_name="Vouchers",
        company_name="$$CurrentCompany",
        fetch_voucher_numbers=False,
    ):
        total = len(xml_list)
        if total == 0:
            return

        TALLY_URL = constants.TALLY_URL + str(constants.TALLY_PORT)
        # ── Adaptive batch size based on total records ──────────────────────
        if total <= 50:
            batch_size = 10
        elif total <= 200:
            batch_size = 25
        elif total <= 1000:
            batch_size = 50
        else:
            batch_size = 100

        # ── Adaptive timeout based on batch size ────────────────────────────
        # ~0.5s per voucher is a safe estimate for Tally processing speed
        def get_timeout(size: int) -> int:
            base = 30  # minimum timeout
            per_rec = 1  # seconds per record
            return max(base, size * per_rec)  # e.g. 50 recs → 50s, 100 recs → 100s

        processed = 0
        consecutive_failures = 0
        MAX_CONSECUTIVE_FAIL = 3

        for i in range(0, total, batch_size):
            batch = xml_list[i : i + batch_size]
            timeout = get_timeout(len(batch))
            envelope = self.build_envelope(
                batch, report_name=report_name, company_name=company_name
            )
            # print(envelope)

            batch_num = i // batch_size + 1

            try:
                res = requests.post(
                    TALLY_URL,
                    data=envelope.encode("utf-8"),
                    headers={"Content-Type": "text/xml"},
                    timeout=timeout,
                )

                response_text = res.text
                if report_name != "All Masters":
                    with open("./lib/tally_errors.txt", "a") as f:
                        f.write(response_text + "\n")
                        print("writing")
                created = self._extract_tag(response_text, "CREATED")
                altered = self._extract_tag(response_text, "ALTERED")
                errors = self._extract_tag(response_text, "ERRORS")

                status_msg = f"📦 Batch {batch_num}/{(total + batch_size - 1) // batch_size} ({len(batch)} recs): "
                if int(errors) > 0:
                    status_msg += f"❌ {errors} Errors | "
                status_msg += f"✅ {created} Created, {altered} Altered"
                print(status_msg)
                LogManagerObj.write_log(status_msg)

                # print(response_text)

                if "<LINEERROR>" in response_text:
                    parts = response_text.split("<LINEERROR>")
                    for idx, part in enumerate(parts[1:20]):  # show max 20 per batch
                        error_detail = html.unescape(part.split("</LINEERROR>")[0])
                        # log_callback(f"   ⚠️ Error {idx + 1}: {error_detail}")
                    # if len(parts) > 6:
                    # log_callback(f"   ... and {len(parts) - 6} more errors")

                    if fetch_voucher_numbers:
                        vnos = [self.get_voucher_number(xml) for xml in batch]
                        # log_callback(f"   📋 Batch vouchers: {', '.join(vnos)}")

                # ── Reset failure counter on success ────────────────────────
                consecutive_failures = 0
                processed += len(batch)
                # progress_callback(processed, total)

                # ── Adaptive sleep: larger batches need more recovery time ──
                sleep_time = (
                    0.3 if len(batch) <= 25 else 0.6 if len(batch) <= 50 else 1.0
                )
                time.sleep(sleep_time)

            except requests.exceptions.Timeout:
                consecutive_failures += 1
                # log_callback(f"⏱️ Batch {batch_num} timed out (waited {timeout}s).")
                LogManagerObj.write_log(
                    f"⏱️ Batch {batch_num} timed out (waited {timeout}s)."
                )

                if consecutive_failures >= MAX_CONSECUTIVE_FAIL:
                    # log_callback(f"❌ {MAX_CONSECUTIVE_FAIL} consecutive timeouts. Tally stopped responding.")
                    # log_callback("💡 Restart Tally and re-run sync — already imported records are safe.")
                    LogManagerObj.write_log(
                        f"❌ {MAX_CONSECUTIVE_FAIL} consecutive timeouts. Tally stopped responding."
                    )
                    break

                # ── Retry once with smaller sub-batches ─────────────────────
                # log_callback(f"🔄 Retrying batch {batch_num} in smaller chunks...")
                half = max(1, len(batch) // 2)
                for j in range(0, len(batch), half):
                    sub_batch = batch[j : j + half]
                    sub_envelope = self.build_envelope(
                        sub_batch, report_name=report_name, company_name=company_name
                    )
                    sub_timeout = get_timeout(len(sub_batch))
                    try:
                        sub_res = requests.post(
                            TALLY_URL,
                            data=sub_envelope.encode("utf-8"),
                            headers={"Content-Type": "text/xml"},
                            timeout=sub_timeout,
                        )
                        sub_text = sub_res.text
                        sub_created = self._extract_tag(sub_text, "CREATED")
                        sub_altered = self._extract_tag(sub_text, "ALTERED")
                        sub_errors = self._extract_tag(sub_text, "ERRORS")
                        # log_callback(f"   ↳ Sub-batch ({len(sub_batch)} recs): ✅ {sub_created} Created, {sub_altered} Altered" +
                        # (f" | ❌ {sub_errors} Errors" if int(sub_errors) > 0 else ""))
                        LogManagerObj.write_log(
                            f"   ↳ Sub-batch ({len(sub_batch)} recs): ✅ {sub_created} Created, {sub_altered} Altered"
                            + (
                                f" | ❌ {sub_errors} Errors"
                                if int(sub_errors) > 0
                                else ""
                            )
                        )
                        consecutive_failures = 0
                    except Exception as sub_e:
                        # log_callback(f"   ↳ Sub-batch failed: {str(sub_e)}")
                        LogManagerObj.write_log(f"   ↳ Sub-batch failed: {str(sub_e)}")
                        pass

                processed += len(batch)
                continue

            except requests.exceptions.ConnectionError:
                consecutive_failures += 1
                # log_callback(f"🔌 Batch {batch_num}: Cannot connect to Tally. Is it running on port 9000?")
                LogManagerObj.write_log(
                    f"🔌 Batch {batch_num}: Cannot connect to Tally. Is it running on port 9000?"
                )
                if consecutive_failures >= MAX_CONSECUTIVE_FAIL:
                    # log_callback("❌ Tally connection lost. Import aborted.")
                    LogManagerObj.write_log("❌ Tally connection lost. Import aborted.")
                    # log_callback("💡 Restart Tally and re-run sync — already imported records are safe.")
                    LogManagerObj.write_log(
                        "💡 Restart Tally and re-run sync — already imported records are safe."
                    )
                    break
                processed += len(batch)
                continue

            except Exception as e:
                consecutive_failures += 1
                # log_callback(f"❌ Batch {batch_num} error: {str(e)}")
                LogManagerObj.write_log(f"❌ Batch {batch_num} error: {str(e)}")
                if consecutive_failures >= MAX_CONSECUTIVE_FAIL:
                    # log_callback("❌ Too many errors. Import aborted.")
                    LogManagerObj.write_log("❌ Too many errors. Import aborted.")
                    break
                processed += len(batch)
                continue

        # log_callback("-" * 50)
        LogManagerObj.write_log("-" * 50)

    def get_companies(self) -> list:
        try:
            xml = """<?xml version="1.0" encoding="utf-8"?>
    <ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>List of Companies</ID>
    </HEADER>
    <BODY>
        <DESC>
        <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
        <TDL>
            <TDLMESSAGE>
            <COLLECTION NAME="List of Companies" ISMODIFY="No" ISFIXED="No" ISINITIALIZE="Yes" ISOPTION="No" ISINTERNAL="No">
                <TYPE>Company</TYPE>
                <NATIVEMETHOD>Name</NATIVEMETHOD>
            </COLLECTION>
            </TDLMESSAGE>
        </TDL>
        </DESC>
    </BODY>
    </ENVELOPE>"""
            TALLY_URL = constants.TALLY_URL + str(constants.TALLY_PORT)
            res = requests.post(
                TALLY_URL,
                data=xml.encode("utf-8"),
                headers={"Content-Type": "text/xml"},
                timeout=5,
            )

            print("Get Companies Response:", res.text)
            companies = re.findall(r'<NAME TYPE="String">(.*?)</NAME>', res.text)
            seen = set()
            unique = []
            for c in companies:
                c = c.strip()
                if c and c not in seen:
                    seen.add(c)
                    unique.append(c)
            return unique if unique else ["$$CurrentCompany"]
        except Exception:
            return ["$$CurrentCompany"]

    def _extract_tag(self, text, tag):
        try:
            if f"<{tag}>" in text:
                return text.split(f"<{tag}>")[1].split(f"</{tag}>")[0]
            return "0"
        except Exception:
            return "0"

    def get_voucher_number(self, xml: str) -> str:
        m = re.search(r"<VOUCHERNUMBER>(.*?)</VOUCHERNUMBER>", xml)
        return m.group(1) if m else "UNKNOWN"

    def check_tally_alive(self) -> bool:
        try:
            xml = """<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Companies</REPORTNAME>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
            TALLY_URL = constants.TALLY_URL + str(constants.TALLY_PORT)
            res = requests.post(
                TALLY_URL,
                data=xml.encode("utf-8"),
                headers={"Content-Type": "text/xml"},
                timeout=5,
            )
            return res.status_code == 200
        except Exception:
            return False

    def export_voucher_register(self, from_date, to_date, company_name):
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Data</TYPE>
    <ID>VoucherReport</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:ASCII</SVEXPORTFORMAT>
        <SVFROMDATE>{from_date.replace("-", "")}</SVFROMDATE>
        <SVTODATE>{to_date.replace("-", "")}</SVTODATE>
        <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>

          <REPORT NAME="VoucherReport">
            <FORMS>VoucherForm</FORMS>
          </REPORT>

          <FORM NAME="VoucherForm">
            <PARTS>VoucherPart</PARTS>
          </FORM>

          <PART NAME="VoucherPart">
            <LINES>VoucherLine</LINES>
            <REPEAT>VoucherLine : VoucherCollection</REPEAT>
            <SCROLLED>Vertical</SCROLLED>
          </PART>

          <LINE NAME="VoucherLine">
            <FIELDS>FldDate,FldParty,FldVchType,FldAmount,FldEmpty,FldVchNo</FIELDS>
          </LINE>

          <FIELD NAME="FldDate">
            <SET>$Date</SET>
          </FIELD>

          <FIELD NAME="FldParty">
            <SET>$PartyLedgerName</SET>
          </FIELD>

          <FIELD NAME="FldVchType">
            <SET>$VoucherTypeName</SET>
          </FIELD>

          <FIELD NAME="FldAmount">
            <SET>$$NumValue:$Amount</SET>
          </FIELD>

          <FIELD NAME="FldEmpty">
            <SET>""</SET>
          </FIELD>

          <FIELD NAME="FldVchNo">
            <SET>"(No. :" + $VoucherNumber + ")"</SET>
          </FIELD>

          <COLLECTION NAME="VoucherCollection">
            <TYPE>Voucher</TYPE>
            <FETCH>Date,PartyLedgerName,VoucherTypeName,VoucherNumber,Amount</FETCH>
          </COLLECTION>

        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
        # print(xml)
        # print(TALLY_URL)
        TALLY_URL = constants.TALLY_URL + str(constants.TALLY_PORT)
        res = requests.post(
            TALLY_URL,
            data=xml.encode("utf-8"),
            headers={"Content-Type": "text/xml"},
            timeout=30,
        )
        # print(res.text)

        if res.status_code != 200:
            raise Exception(f"Tally export failed: {res.text}")

        return res.text
