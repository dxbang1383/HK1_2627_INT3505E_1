
USERS = {
    1: {
        "id": 1,
        "f": "Van",
        "l": "Nguyen",
        "first_name": "Van",
        "last_name": "Nguyen",
        "email": "van.nguyen@example.com",
    },
    2: {
        "id": 2,
        "f": "Thi",
        "l": "Tran",
        "first_name": "Thi",
        "last_name": "Tran",
        "email": "thi.tran@example.com",
    },
}

def get_user(uid: int):
    return USERS.get(uid)
