from flask import Flask
import math, requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

TOKEN = '8047332194:AAHGDD1IRnJh-rvasMxLSt7SfMLJMmPCiqc'
CHAT_ID = 'me'

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

def fetch_powerball_results():
    url = "https://bepick.net/game/default/dhrpowerball"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")
    elements = soup.select("div.noflf")
    numbers = [int(el.text.strip()) for el in elements if el.text.strip().isdigit()]
    return numbers[:15]

def analyze(numbers):
    count, freq, appearance = {}, {}, {}
    for n in numbers: count[n] = count.get(n, 0) + 1
    for i in range(10): freq[i] = count.get(i, 0) / len(numbers)
    score = 0
    for n in numbers:
        appearance[n] = appearance.get(n, 0) + 1
        base = 1 if n <= 4 else -1
        t = appearance[n]
        weight = 1.0 if t == 1 else 0.7 if t == 2 else 1.0 if t == 3 else 1.3 if t == 4 else 1.5
        adj = 1 - (freq[n] - 0.1)
        score += base * weight * adj
    tc = score / math.sqrt(len(numbers))
    pu = min(max(0.5 + tc * 0.02, 0), 1)
    po = 1 - pu
    eu = pu * 1.95 - (1 - pu)
    eo = po * 1.95 - (1 - po)
    def kelly(p): return max(0, ((0.95 * p) - (1 - p)) / 0.95)
    ku, ko = kelly(pu), kelly(po)
    pick, msg = '보류', ''
    if pu >= 0.515 and eu > eo + 0.01:
        pick = '언더'
        msg = f"[SoftBayes]\n추천: {pick}\n승률: {pu*100:.1f}%\nEV: {eu:.3f}\n켈리: 자산의 {ku*100:.1f}%"
    elif po >= 0.515 and eo > eu + 0.01:
        pick = '오버'
        msg = f"[SoftBayes]\n추천: {pick}\n승률: {po*100:.1f}%\nEV: {eo:.3f}\n켈리: 자산의 {ko*100:.1f}%"
    if msg:
        send_telegram_message(msg)

@app.route('/')
def run_softbayes():
    try:
        nums = fetch_powerball_results()
        analyze(nums)
        return "OK"
    except Exception as e:
        return f"ERR: {str(e)}"

if __name__ == '__main__':
    app.run()
