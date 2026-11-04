# Map of URLs, routes, and templates

| URL                 | Flask routes.py | HTML Template |
| ------------------- | ------------------------------- | ---------------------------------------- |
| /poweruser          | main/routes/poweruser.py        | main/templates/poweruser.html            |
| /gast               | main/routes/gast.py             | main/templates/gast.html                 |
| /user_order_history | main/routes/order_history.py    | main/templates/orders_history.html       |
||
| /feedback/N         | orders/routes/feedback.py       | main/templates/observation_feedback.html |
| /orders             | orders/routes/order_list.py     | orders/templates/orders.html             |
| /order/N/edit       | orders/routes/edit_order_pos.py | orders/templates/edit_order_pos.py       |
||
| /post/N             | posts/routes.py                 | posts/templates/post.html                |
