# G1 – Completion Summary (Data and Method Audit)

**Trạng thái:** Các kiểm tra G1.1–G1.4 đã có kết quả và tài liệu tổng hợp; G1 có thể chuyển sang trạng thái hoàn tất có điều kiện sau khi lưu bằng chứng chạy cuối cùng của split verifier.

## G1.1 – Dataset provenance and license

- Dataset MQM: `newstest2020/ende/mqm_newstest2020_ende.tsv` từ repository `google/wmt-mqm-human-evaluation`.
- Repository root license được xác định là Apache License 2.0.
- Đã đối chiếu mapping và 7 MT outputs với official WMT20 archive: 8/8 file khớp chính xác.
- SHA-256 và manifest nguồn được lưu trong `reports/source_file_manifest.csv` và `reports/dataset_license_audit.md`.
- Giới hạn: không suy rộng license ở cấp repository thành cam kết rằng mọi thành phần dữ liệu bên thứ ba đều có thể tái phân phối không hạn chế.

## G1.2 – Data structure and quality

- MQM: 79.020 annotation rows, 9 columns.
- 7 hệ thống MT được dùng cho mô hình; 130 documents; 1.418 segments mỗi hệ thống.
- 9.926 MT system-segment examples.
- Không có missing values trong các trường đã kiểm tra; không có exact duplicate rows.
- Mapping được đối chiếu theo khóa document/line đã sửa đúng: 79.020/79.020 annotation rows matched.
- Source nhất quán giữa các hệ thống.
- So sánh MQM target với original MT outputs cho thấy 7.838 all-match, 2.072 some-match và 16 none-match; original MT outputs được dùng làm target đầu vào mô hình.

## G1.3 – Label definition audit

- Critical annotation: severity Major và category thuộc `Accuracy/*` hoặc `Non-translation!`.
- Một rater chỉ đóng góp tối đa một phiếu cho mỗi segment.
- Nhãn dương khi ít nhất 2/3 raters bỏ phiếu serious.
- 9.926 segments đều có 3 raters.
- Nhãn: 1.183 Critical (11,92%), 8.743 non-Critical.
- Phân phối phiếu: 0 votes = 6.810; 1 = 1.933; 2 = 846; 3 = 337.
- Trường hợp sơ bộ từng bị báo 2 raters đã được giải quyết bằng cách đọc lại với đúng parser pipeline; thực tế có 3 raters.

## G1.4 – Feature provenance and leakage

Đã kiểm tra:
- `src/run_baselines.py`
- `src/run_ablation_dev.py`
- `src/evaluate_test_week10.py`
- `src/split_by_document.py`
- `src/verify_locked_split.py`
- `experiments/sensitivity_analysis_week10.py`
- `src/build_model_dataset.py`

Kết luận:
- Baseline chính dùng TF-IDF source + target và 12 surface features.
- Không thấy `y_primary`, `serious_votes`, `distinct_raters`, `category`, `severity` hoặc `rater` trong feature matrix.
- TF-IDF/scaler fit trên Train trong development; Test evaluation fit trên Train+Dev và transform Test.
- Ablation system identity được fit trên Train; đây là cấu hình riêng.
- Document split dùng GroupShuffleSplit theo `doc` và kiểm tra overlap.
- Không phát hiện label leakage hoặc preprocessing leakage trực tiếp trong các mã nguồn đã kiểm tra.

## G1 – Kết luận tổng hợp

Phạm vi nghiên cứu, dữ liệu, quy tắc nhãn, nguồn gốc feature và các bước ngăn leakage đã được mô tả và kiểm tra ở cấp mã nguồn. Bộ dữ liệu mô hình có 9.926 phân đoạn MT từ 7 hệ thống trên 130 tài liệu. Nhãn Critical chiếm 11,92%, được xác định bằng ngưỡng đồng thuận ít nhất 2/3 người chấm.

Các kiểm tra hiện tại hỗ trợ việc chuyển sang giai đoạn đánh giá thực nghiệm G2. Tuy nhiên, trước khi tuyên bố G1 hoàn tất tuyệt đối, cần lưu stdout của `verify_locked_split.py` trên đúng snapshot đang dùng và bảo đảm kết quả hash/assignments khớp. Nên thống nhất cấu hình đọc MQM giữa các script tái dựng nhãn và error analysis.

## Các tài liệu G1 nên lưu trong `reports/`

- `dataset_license_audit.md`
- `data_quality_audit.md`
- `label_definition_audit.md`
- `feature_provenance_audit.md`
- `data_leakage_audit.md`
- `G1_completion_summary.md`
- `source_file_manifest.csv`
