-- Migration: insert_health_mock_data_alerts
-- Created at: 1763373406

INSERT INTO health_alerts (user_id, alert_type, severity, indicator_name, abnormal_value, normal_range, risk_assessment, recommended_actions, acknowledged, resolved) VALUES
('7885af30-efd1-4904-b2a7-06feac81ee32', 'blood_pressure_high', 'medium', '心率', '105', '3.9-6.1', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('e9ee8027-1f4e-4ce3-987f-7b205a6a01d6', 'blood_glucose_high', 'high', '心率', '105', '<140/90', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('695ac55d-6b5a-4af6-94fb-d5421a34a588', 'heart_rate_abnormal', 'medium', '心率', '165/105', '3.9-6.1', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('bd790ed9-fb4c-4f3d-b31b-9ac4ba354307', 'heart_rate_abnormal', 'medium', '心率', '8.5', '60-100', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('b9cdb80b-9e8c-440e-aa99-f106a0447071', 'blood_glucose_high', 'medium', '血糖', '8.5', '<140/90', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('462d8370-89c3-4704-aaea-4825cae9d70d', 'blood_pressure_high', 'medium', '血压', '165/105', '60-100', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('46796037-60d5-4a71-a2c6-d87f7df7c80f', 'blood_glucose_high', 'high', '血压', '165/105', '3.9-6.1', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('474bbd6d-2da5-40c3-875b-d2d3f229e6d7', 'blood_glucose_high', 'high', '血压', '8.5', '3.9-6.1', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('fcbc3f1e-320d-4768-a4e1-9bc001b295af', 'blood_glucose_high', 'medium', '血糖', '8.5', '60-100', '指标异常需要关注', '建议就医检查或联系医生', false, false),
('4b3d61b8-9a98-4c11-be4e-1a2269bf2cbb', 'blood_glucose_high', 'high', '血压', '8.5', '3.9-6.1', '指标异常需要关注', '建议就医检查或联系医生', false, false);;