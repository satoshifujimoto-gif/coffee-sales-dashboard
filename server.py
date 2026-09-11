"""Coffee sales dashboard server.

Combines the Jan-Mar and Apr-Jun sales CSVs and serves them as JSON at
/api/sales, and serves server_dashboard.html (which fetches that endpoint)
at /. Standard library only -- no pip install required.

Run:
    python server.py
Then open:
    http://127.0.0.1:8000
"""
import csv
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILES = ["売上データ.csv", "売上データ_4-6月.csv", "売上データ_7月.csv"]
DASHBOARD_FILE = "server_dashboard.html"
HOST, PORT = "127.0.0.1", 8000


def load_sales():
    rows = []
    for filename in CSV_FILES:
        path = os.path.join(BASE_DIR, filename)
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rows.append({
                    "date": row["日付"],
                    "product": row["商品名"],
                    "category": row["カテゴリ"],
                    "region": row["地域"],
                    "qty": int(row["数量"]),
                    "price": int(row["単価"]),
                    "amount": int(row["売上金額"]),
                })
    rows.sort(key=lambda r: r["date"])
    return rows


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body_bytes, content_type, cors=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body_bytes)))
        if cors:
            # Lets the dashboard HTML fetch this endpoint when opened directly
            # from disk (file://) instead of through this server.
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain", cors=True)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/sales":
                data = load_sales()
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8", cors=True)
            elif path in ("/", "/index.html"):
                file_path = os.path.join(BASE_DIR, DASHBOARD_FILE)
                with open(file_path, encoding="utf-8") as f:
                    body = f.read().encode("utf-8")
                self._send(200, body, "text/html; charset=utf-8")
            else:
                self._send(404, b"Not Found", "text/plain; charset=utf-8")
        except FileNotFoundError as e:
            self._send(500, f"Server error: {e}".encode("utf-8"), "text/plain; charset=utf-8")

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"売上データAPIサーバーを起動しました: http://{HOST}:{PORT}")
    print(f"読み込むCSV: {', '.join(CSV_FILES)}")
    print("Ctrl+C で停止します。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止しました。")
