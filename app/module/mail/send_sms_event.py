# import ovh
#
#
# def send_sms_event(event, mail_type):
#     client = ovh.Client(
#         endpoint='ovh-eu',
#         application_key='TON_APP_KEY',
#         application_secret='TON_SECRET',
#         consumer_key='TON_CONSUMER_KEY',
#     )
#
#     message = choix_sms_message(event, mail_type)
#     response = client.post('/sms/mon-service-name/jobs', {
#         'receivers': [event.client.numero_telephone],
#         'message': message,
#         'sender': 'MySelfieBt',  # nom affiché
#         'priority': 'high',
#     })
#     print("SMS envoyé :", response)
#
#
# def choix_sms_message(event, mail_type):
#     if mail_type == 'relance_avis':
#         message = (
#             f"Merci {event.client.nom} pour votre confiance !\n"
#             "Laissez-nous un avis :\n"
#             "https://g.page/r/CWmORCsX-piOEAE/review\n"
#             "📸 MySelfieBooth"
#         )
#         return message
