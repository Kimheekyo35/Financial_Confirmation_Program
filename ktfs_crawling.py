from playwright.sync_api import sync_playwright
import json
# 총 데이터가 26634건이 됨.
# 여기에서 26634건을 가져오기 위해서는 페이지를 이동하면서 데이터를 가져와야 함.
# search_input에서 value 값을 input_box_list에 넣고, 병렬로 데이터를 가져오도록 해야 함.

# 모든 데이터 담기

pass_value = [
    '001', '002', '003', '004', '007', '008', '011', '012',
    '020', '023', '027', '030', '031', '032', '034', '035',
    '037', '039', '045', '048', '050', '052', '054', '055',
    '057', '058', '059', '060', '061', '062', '063', '064',
    '065'
]

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
        if value in pass_value:
            continue
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
                    "bank_name": cleaned_data[0],
                    "branch_name": cleaned_data[1],
                    "branch_code" : cleaned_data[2],
                    "address_code": cleaned_data[3],
                    "address": cleaned_data[4],
                    "call_number": cleaned_data[5],
                    "fax_number" : cleaned_data[6],
                    "separate" : cleaned_data[7]
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

