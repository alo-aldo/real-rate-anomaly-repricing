#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_data.py — OSAP 데이터 자동 다운로드 (공식 openassetpricing 패키지)

사용법:
  pip install openassetpricing pandas
  python download_data.py

성공 시 생성:
  data/PredictorLSretWide.csv   (신호별 롱숏 월수익률)
  data/SignalDoc.csv            (신호 메타데이터)

실패 시: 콘솔에 수동 다운로드 안내가 출력됩니다.
※ 구글드라이브에서 받아오므로 일반 인터넷 환경이면 됩니다.
"""
import os
import re
import sys

os.makedirs("data", exist_ok=True)

MANUAL = """
[수동 다운로드 안내]
1) https://www.openassetpricing.com -> Data 메뉴
2) Portfolio Returns 중 'Predictor' 롱숏 월수익률 CSV
   -> data/PredictorLSretWide.csv 로 저장
   (wide/long 어느 포맷이든 됩니다 - 분석 스크립트가 자동 처리)
3) SignalDoc.csv 는 함께 전달받은 파일을 data/ 에 복사
"""


def main():
    try:
        import openassetpricing as oap
    except ImportError:
        print("먼저 실행: pip install openassetpricing")
        sys.exit(1)

    try:
        openap = oap.OpenAP()  # 최신 릴리스
    except Exception as e:
        print("릴리스 정보를 가져오지 못했습니다:", str(e)[:150])
        print(MANUAL)
        sys.exit(1)

    # 1) 사용 가능한 포트 데이터 목록에서 롱숏(wide) 후보 찾기
    try:
        ports = openap.list_port()
        names = [str(x) for x in
                 (ports if isinstance(ports, (list, tuple)) else list(ports))]
    except Exception as e:
        names = []
        print("[warn] list_port 실패:", str(e)[:100])
    print("사용 가능한 포트 데이터:", names)

    prefer = [n for n in names if re.search(r"ls.*wide|wide.*ls", n, re.I)]
    prefer += [n for n in names if re.search(r"^op$|predictor", n, re.I)]
    prefer = list(dict.fromkeys(prefer))  # 중복 제거, 순서 유지

    if not prefer:
        print("\n자동 매칭 실패 — 출력된 포트 데이터 목록에서 Predictor 또는"
              " long-short wide 형식에 해당하는 이름을 확인해 주세요.")
        print(MANUAL)
        sys.exit(1)

    df = None
    for name in prefer:
        try:
            print(f"[try] dl_port('{name}') ...")
            df = openap.dl_port(name, "pandas")
            print(f"[ok] '{name}' 다운로드 완료: {df.shape}")
            break
        except Exception as e:
            print(f"[fail] {name}: {str(e)[:100]}")
    if df is None:
        print("자동 다운로드 실패.")
        print(MANUAL)
        sys.exit(1)

    df.to_csv(os.path.join("data", "PredictorLSretWide.csv"), index=False)
    print("[saved] data/PredictorLSretWide.csv")

    # 2) SignalDoc
    try:
        doc = openap.dl_signal_doc("pandas")
        doc.to_csv(os.path.join("data", "SignalDoc.csv"), index=False)
        print("[saved] data/SignalDoc.csv")
    except Exception as e:
        print("[warn] SignalDoc 자동 다운로드 실패 — 전달받은 SignalDoc.csv를"
              " data/ 에 복사하세요.", str(e)[:80])

    print("\n완료! 다음 단계:  python regime_rotation_pilot.py")


if __name__ == "__main__":
    main()
