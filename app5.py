from flask import Flask, jsonify
app = Flask(__name__)

ORDERS = {} 

@app.route("/orders/<id>", methods=["DELETE"]) 
def delete_order(order_id): 
    order = ORDERS.get(order_id) 

    if not order: 
        return jsonify({"error": "not found"}), 404
    if order["status"] in ("shipped", "delivered"):
        return jsonify({"error" : "can not delete"}), 409
    
    ORDERS.pop(order)
    return jsonify(""), 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)