# users_data.py - Nguồn dữ liệu người dùng dùng chung cho các version

USERS = {
    1: {
        "id": 1,
        "f": "Văn",
        "l": "Nguyễn",
        "first_name": "Văn",
        "last_name": "Nguyễn",
        "email": "van.nguyen@example.com",
    },
    2: {
        "id": 2,
        "f": "Thị",
        "l": "Trần",
        "first_name": "Thị",
        "last_name": "Trần",
        "email": "thi.tran@example.com",
    },
}

def get_user(uid: int):
    return USERS.get(uid)
