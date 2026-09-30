# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Trần Vũ Gia Huy
- **MSSV:** 2A202602705
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/jerrygiahuy/K4-L3-DAY13-TranVuGiaHuy-2A202602705-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602705`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Sau CP1 có 11 correlation ID duy nhất, đủ enrichment và không có PII leak |
| `validate_dashboard.py` | 6/6 | 6/6 | Đủ latency, traffic, errors/retrieval, cost, tokens và quality |
| `pytest` | 22 passed | 26 passed | Bổ sung test PII và child observations retrieval/generation |
| Số traces hợp lệ | 0 | | Chưa cấu hình Langfuse key ở thời điểm đo baseline |
| Số PII leak | 0 | 0 | Quét độc lập email, điện thoại VN, CCCD và thẻ thanh toán |
| Latency P95 / TTFT P95 | 160 ms / 56 ms | | Tính từ `data/logs.jsonl` sau workload baseline |
| Retrieval success rate | | | |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa context cũ ở đầu request, ưu tiên `x-request-id` do client gửi; nếu thiếu thì sinh `req-` cùng 8 ký tự hex. ID được bind vào structlog context, lưu tại `request.state`, trả lại qua header `x-request-id` và xuất hiện trong mọi log của request.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`, event, timestamp, level; response còn có latency, TTFT, token, cost, quality và trạng thái retrieval.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` duyệt đệ quy toàn bộ giá trị string trong event dictionary và chạy trước `JsonlFileProcessor` lẫn JSON renderer. User ID chỉ được ghi dưới dạng SHA-256 rút gọn.
- **Cách kiểm chứng kết quả:** Gửi request chứa email, điện thoại VN, CCCD và thẻ giả lập; header trả đúng `req-abcdef12` cùng response time. Quét raw log không thấy giá trị gốc, chỉ thấy marker `REDACTED_*`; `validate_logs.py` đạt 100/100 và pytest đạt 24/24.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Chờ cấu hình key của project `day13-k4-l3b-2A202602705`; sẽ đối chiếu số request trong log với trace list và kiểm tra metadata project trước khi chụp evidence.
- **Cấu trúc root/retrieval/generation observations:** Root trace `day13-agent-request` chứa agent observation `lab-agent-run`; bên trong có `retrieval` loại retriever và `generation` loại generation. Retrieval chỉ lưu query preview đã scrub cùng doc count; generation không capture raw input/output nhưng ghi model, usage, cost, preview đã scrub và managed prompt object.
- **Cách nối trace với log:** `correlation_id` được bind từ middleware, truyền vào `LabAgent.run` và đặt trong trace metadata; tìm cùng giá trị đó trong structured log và Langfuse.
- **Prompt name:** `day13-chat`
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard contract có đúng sáu panel: latency P50/P95/P99 và TTFT; traffic theo phút; error rate cùng retrieval success trên mọi event có `tool_success`; cost; input/output tokens; quality proxy. Mỗi panel có nguồn, query, đơn vị, cửa sổ 60 phút, refresh 30 giây và threshold.
- **SLO và lý do chọn:** 99.5% request trong cửa sổ 28 ngày phải có `response_sent` và latency không quá 3000 ms. Baseline P95 khoảng 160 ms; ngưỡng 3000 ms tạo khoảng đệm cho tải và dependency ngoài nhưng vẫn phản ánh trải nghiệm chậm rõ rệt.
- **Cách tính error budget:** Phần không đạt cho phép là `100% - 99.5% = 0.5%`; với 10,000 request thì `10,000 × 0.005 = 50` request được phép lỗi hoặc chậm hơn ngưỡng.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` (>3000 ms trong 5m), `HighRequestErrorRate` (>2% trong 5m) và `LowRetrievalSuccessRate` (<90% trong 10m). Cả ba gửi Slack `#k4-l3b-alerts`, có severity/owner và runbook Metrics → Logs → Traces cùng mitigation tại `docs/alerts.md`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
