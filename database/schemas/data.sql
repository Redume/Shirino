CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    chart BOOLEAN DEFAULT 1,
    chart_period TEXT DEFAULT 'month',
    lang TEXT DEFAULT 'en'
);
