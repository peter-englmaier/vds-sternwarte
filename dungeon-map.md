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

| routex.py | Path |
| --------- | ---- |
| webapp/inout/routes.py                            | /inout/export
| webapp/inout/routes.py                            | /inout/import
| webapp/posts/routes.py	                        | /post/new
| webapp/posts/routes.py                            | /post/&lt;int:post_id&gt;
| webapp/posts/routes.py	                        | /post/&lt;int:post_id&gt;/update
| webapp/posts/routes.py	                        | /post/&lt;int:post_id&gt;/delete
| webapp/users/routes.py	                        | /register
| webapp/users/routes.py	                        | /login
| webapp/users/routes.py:                           | /logout
| webapp/users/routes.py	                        | /account
| webapp/users/routes.py                            | /password_changed
| webapp/users/routes.py                            | /user/&lt;string:username&gt;
| webapp/users/routes.py	                        | /reset_password
| webapp/users/routes.py	                        | /reset_password/&lt;token&gt;
| webapp/main/routes/about.py                       | /about
| webapp/main/routes/approver.py	                | /approver
| webapp/main/routes/faq.py                         | /faq
| webapp/main/routes/fg_request.py                  | /fgrequest
| webapp/main/routes/fg_request.py                  | /add-row
| webapp/main/routes/gast.py	                    | /gast
| webapp/main/routes/gast.py	                    | /gast/approve
| webapp/main/routes/home.py                        | /
| webapp/main/routes/home.py                        | /home
| webapp/main/routes/home.py                        | /status
| webapp/main/routes/impressum.py                   | /impressum
| webapp/main/routes/observation_database.py        | /observationlist_complete
| webapp/main/routes/order_history.py               | /user_order_history
| webapp/main/routes/poweruser_history.py           | /poweruser_order_history
| webapp/main/routes/poweruser.py	                | /poweruser
| webapp/main/routes/request_georg.py               | /request_georg"
| webapp/main/routes/service_request.py             | /servicerequest
| webapp/orders/routes/api.py	                    | /orders/user_preference
| webapp/orders/routes/api.py	                    | /orders/user_preference
| webapp/orders/routes/api.py                       | /orders/get_telescopes/&lt;int:observatory_id&gt;
| webapp/orders/routes/api.py	                    | /orders/get_filtersets
| webapp/orders/routes/approval.py	                | /poweruser/&lt;int:order_id&gt;/pu_accept
| webapp/orders/routes/approval.py	                | /approver/assign_poweruser
| webapp/orders/routes/approval.py	                | /approver/&lt;int:order_id&gt;/approve
| webapp/orders/routes/approval.py	                | /approver/assign_poweruser_form
| webapp/orders/routes/calendar.py	                | /orders/show_calendar
| webapp/orders/routes/create_order.py	            | /actionhandler
| webapp/orders/routes/edit_order_pos.py	        | /orders/&lt;int:order_id&gt;/edit
| webapp/orders/routes/feedback.py                  | /feedback/&lt;int:feedback_id&gt;
| webapp/orders/routes/feedback.py                  | /feedback/&lt;int:feedback_id&gt;/cancel
| webapp/orders/routes/obs_request_complete.py      | /obs_requests
| webapp/orders/routes/obs_request_complete.py      | /order_history
| webapp/orders/routes/order_list.py	            | /orders
| webapp/orders/routes/order_list.py	            | /orders/&lt;int:order_id&gt;/copy_order
| webapp/orders/routes/order_list.py	            | /orders/&lt;int:order_id&gt;/delete_order
| webapp/orders/routes/order_positions.py           | /orders/&lt;int:order_id&gt;/positions
| webapp/orders/routes/order_positions.py           | /orders/&lt;int:order_id&gt;/reservation.ics
| webapp/orders/routes/reject_order.py	            | /approver/&lt;int:order_id&gt;/reject
| webapp/orders/routes/status_flow.py	            | /orders/status
