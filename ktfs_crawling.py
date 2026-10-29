from playwright.sync_api import sync_playwright
import json
import re
import unicodedata

# 데이터 저장할 때 정규화 진행하기
def normalize_dictionary_data(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="msedge",
        headless=False
    )

    page = browser.new_page()
    page.goto("https://www.kftc.or.kr/archive/bankListByName")


    # 검색어 구분 클릭하는 부분
    search_input = page.locator("div[class='input_box'] > select[title='검색어 구분']")
    search_input.click()

    # option의 value값을 넣는 리스트 (ex: 수출입, 농협이 어떤 value를 가지고 있는지 확인)
    search_value_name_dict = {}
    
    options = search_input.locator("option")

    for option in options.all():
        value = option.get_attribute("value")
        name = option.inner_text().strip()
        if value =="000":
            pass
        else:
            search_value_name_dict[value] = name

    print(search_value_name_dict)

    # 금융회사명 조회
    for value, name in search_value_name_dict.items():
        # if value in pass_value:
        #     continue
        all_data = []  # 각 금융회사명 조회 시마다 데이터를 담을 리스트 초기화

        search_input = page.locator("div[class='input_box'] > select[title='검색어 구분']")
        search_input.select_option(value)
        page.wait_for_timeout(1000)

        print(f"금융회사명 조회: {name} ({value})")

        # 조회 버튼 누르기
        search_button = page.locator("button[type='submit']")
        search_button.click()
        page.wait_for_timeout(2000)

        # 페이지 이동하면서 데이터 가져오기
        next_button = page.locator("button[aria-label='다음으로']")
        
        # 다음페이지 버튼 누를 수 있을 때까지 반복
        while True:
            # tr의 개수
            tr = page.locator("div.board_table.scrollbar > table > tbody > tr")
            
            if next_button.count() == 0:
                print(f"{name} ({value}) 조회 결과 없음")
                break

            for i in range(tr.count()):
                # tr의 td 가져오기
                td = tr.nth(i).locator("td")
                data = [td.nth(j).inner_text() for j in range(td.count())]
                cleaned_data = [" ".join(d.split()) for d in data]  # \u3000 제거
                
                if len(cleaned_data) < 8:
                      # 데이터가 부족하면 건너뜀
                    continue

                dictionary_data = {
                    "bank_name": normalize_dictionary_data(cleaned_data[0]),
                    "branch_name": normalize_dictionary_data(cleaned_data[1]),
                    "branch_code": normalize_dictionary_data(cleaned_data[2]),
                    "address_code": normalize_dictionary_data(cleaned_data[3]),
                    "address": normalize_dictionary_data(cleaned_data[4]),
                    "call_number": normalize_dictionary_data(cleaned_data[5]),
                    "fax_number" : normalize_dictionary_data(cleaned_data[6]),
                    "separate" : normalize_dictionary_data(cleaned_data[7])
                }

                all_data.append(dictionary_data)  # 데이터를 리스트에 추가
            
            # 현재 페이지 다 읽은 후, 다음 button이 disabled인지 확인하고, disabled이면 break
            if next_button.is_disabled():
                break

            # 다음 페이지 버튼 클릭
            next_button.click()
            page.wait_for_timeout(1000)

        with open(f"financial_json_dir/{name}_{value}.json", "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)

            print(f"총 {len(all_data)}건 저장 완료")

    browser.close()

