from data_fetcher import fetch_data, write_data

# 调用 fetch_data 并打印结果
if __name__ == "__main__":
    data = fetch_data()
    new_data = {
        'content': 'This is a new entry',
        'source: 'python'
    }
    write_data(new_data)