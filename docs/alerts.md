# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của các event `response_sent` và SLO request hoàn tất trong 3000 ms.
- Điều kiện và thời gian duy trì: `p95(response_sent.latency_ms) > 3000` liên tục 5 phút.
- Ảnh hưởng tới người dùng: câu trả lời đến chậm, làm tăng thời gian chờ và có thể gây timeout phía client.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency, xác nhận P95/P99 và TTFT tăng trong cùng khoảng thời gian.
  2. Lọc log `response_sent` có latency cao, lấy một `correlation_id` đại diện.
  3. Mở trace cùng ID, so sánh thời gian child observation retrieval và generation.
- Mitigation tạm thời: tắt practice incident nếu đang bật; rollback prompt vừa promote nếu generation tăng; giảm tải hoặc khôi phục dependency retrieval theo span gây chậm.
- Owner: `student-2A202602705`

## Alert 2

- Tên: `HighRequestErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỷ lệ request thành công; guardrail error rate tối đa 2%.
- Điều kiện và thời gian duy trì: `request_error_rate_pct > 2` liên tục 5 phút.
- Ảnh hưởng tới người dùng: một phần request `/chat` trả lỗi thay vì câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors để xác nhận tỷ lệ và thời điểm error tăng.
  2. Nhóm `request_failed` theo `error_type`, chọn một log và lấy `correlation_id`.
  3. Mở trace cùng ID, xác định retrieval hay generation kết thúc ở trạng thái lỗi.
- Mitigation tạm thời: rollback thay đổi gần nhất; vô hiệu hóa scenario lỗi; chuyển sang local prompt fallback hoặc khôi phục dependency gây lỗi.
- Owner: `student-2A202602705`

## Alert 3

- Tên: `LowRetrievalSuccessRate`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: retrieval success guardrail tối thiểu 90%.
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90` liên tục 10 phút.
- Ảnh hưởng tới người dùng: câu trả lời thiếu context hoặc request thất bại dù API vẫn có thể phản hồi.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors và xác nhận retrieval success giảm trong cửa sổ cảnh báo.
  2. Lọc mọi event có `tool_name=retrieval`, chọn record `tool_success=false` và lấy `correlation_id`.
  3. Mở trace cùng ID, kiểm tra child observation retrieval, doc count và status message.
- Mitigation tạm thời: tắt incident retrieval, kiểm tra nguồn dữ liệu/index và dùng fallback an toàn trong lúc khôi phục.
- Owner: `student-2A202602705`
