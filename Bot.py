import telebot
from telebot import types
from collections import defaultdict

TOKEN = "TON_TOKEN_ICI"  # ← Remplace

bot = telebot.TeleBot(TOKEN)

# Stockage simple du panier (user_id -> {product: quantity})
carts = defaultdict(dict)

# ==================== PRODUITS EXEMPLES ====================
products = {
    "otacos": [
        {"name": "Tacos Classique", "price": 8.90},
        {"name": "Tacos Poulet", "price": 9.90},
        {"name": "Frites", "price": 3.50},
    ],
    "pizzatime": [
        {"name": "Margherita", "price": 10.90},
        {"name": "Pepperoni", "price": 12.90},
        {"name": "Boisson", "price": 2.50},
    ],
    "chamas": [
        {"name": "Burrito Boeuf", "price": 9.50},
        {"name": "Quesadilla", "price": 8.90},
    ],
    "pitaya": [
        {"name": "Açaï Bowl", "price": 7.90},
        {"name": "Smoothie", "price": 5.90},
    ],
    "divers": [
        {"name": "Hot Dog", "price": 4.50},
        {"name": "Croissant", "price": 2.20},
    ],
    "traidinn": [
        {"name": "Burger Classique", "price": 11.90},
        {"name": "Chicken Burger", "price": 10.90},
    ]
}

# ==================== MENUS ====================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Nos produits", callback_data="menu_produits"),
        types.InlineKeyboardButton("💰 Recharger", callback_data="menu_recharger")
    )
    return markup

def produits_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌮 O’Tacos", callback_data="cat_otacos"),
        types.InlineKeyboardButton("🍕 Pizza Time", callback_data="cat_pizzatime"),
        types.InlineKeyboardButton("🌯 Chamas Tacos", callback_data="cat_chamas"),
        types.InlineKeyboardButton("🥑 Pitaya", callback_data="cat_pitaya"),
        types.InlineKeyboardButton("🍟 Divers Snack", callback_data="cat_divers"),
        types.InlineKeyboardButton("🍔 Traidinn", callback_data="cat_traidinn")
    )
    markup.add(types.InlineKeyboardButton("🔙 Retour Accueil", callback_data="back_main"))
    return markup

def category_menu(category):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(products.get(category, [])):
        markup.add(types.InlineKeyboardButton(
            f"{p['name']} - {p['price']}€", 
            callback_data=f"add_{category}_{i}"
        ))
    markup.add(types.InlineKeyboardButton("🛍 Voir mon panier", callback_data="view_cart"))
    markup.add(types.InlineKeyboardButton("🔙 Retour Produits", callback_data="menu_produits"))
    return markup

def cart_text(user_id):
    cart = carts[user_id]
    if not cart:
        return "Votre panier est vide 🛒"
    total = 0
    lines = ["🛍 **Votre Panier**\n"]
    for item, qty in cart.items():
        price = next((p['price'] for cat in products.values() for p in cat if p['name'] == item), 0)
        subtotal = price * qty
        total += subtotal
        lines.append(f"{qty}x {item} → {subtotal:.2f}€")
    lines.append(f"\n**Total : {total:.2f}€**")
    return "\n".join(lines)

# ==================== START ====================
@bot.message_handler(commands=['start'])
def start(message):
    text = "👋 **Bonjour et bienvenue sur le bot !**\n\nQue souhaitez-vous faire ?"
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())

# ==================== CALLBACKS ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    user_id = call.from_user.id

    if call.data == "menu_produits":
        bot.edit_message_text("🛒 **Nos Produits**\nChoisissez votre enseigne :", 
                              chat_id, msg_id, reply_markup=produits_menu(), parse_mode='Markdown')

    elif call.data == "menu_recharger":
        bot.edit_message_text("💰 **Recharger votre solde**\n\nFonctionnalité bientôt disponible.", 
                              chat_id, msg_id, reply_markup=main_menu())

    elif call.data.startswith("cat_"):
        cat = call.data[4:]
        bot.edit_message_text(f"📋 **{cat.upper()}**\nSélectionnez un produit :", 
                              chat_id, msg_id, reply_markup=category_menu(cat), parse_mode='Markdown')

    elif call.data.startswith("add_"):
        _, cat, idx = call.data.split("_")
        idx = int(idx)
        product = products[cat][idx]
        name = product["name"]
        
        if name in carts[user_id]:
            carts[user_id][name] += 1
        else:
            carts[user_id][name] = 1
        
        bot.answer_callback_query(call.id, f"✅ {name} ajouté au panier !")

    elif call.data == "view_cart":
        text = cart_text(user_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛍 Commander", callback_data="checkout"))
        markup.add(types.InlineKeyboardButton("🗑 Vider le panier", callback_data="clear_cart"))
        markup.add(types.InlineKeyboardButton("🔙 Continuer mes achats", callback_data="menu_produits"))
        
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode='Markdown')

    elif call.data == "clear_cart":
        carts[user_id].clear()
        bot.answer_callback_query(call.id, "Panier vidé !")
        bot.edit_message_text(cart_text(user_id), chat_id, msg_id, 
                              reply_markup=types.InlineKeyboardMarkup().add(
                                  types.InlineKeyboardButton("🔙 Retour", callback_data="menu_produits")
                              ), parse_mode='Markdown')

    elif call.data == "checkout":
        cart = carts[user_id]
        if not cart:
            bot.answer_callback_query(call.id, "Panier vide !")
            return
        
        total = 0
        description = []
        for item, qty in cart.items():
            price = next((p['price'] for cat in products.values() for p in cat if p['name'] == item), 0)
            subtotal = price * qty
            total += subtotal
            description.append(f"{qty}x {item}")

        # Envoi de la facture (remplace PROVIDER_TOKEN par le tien)
        bot.send_invoice(
            chat_id=chat_id,
            title="Commande Food Bot",
            description="\n".join(description),
            payload="food_order_" + str(user_id),
            provider_token="PROVIDER_TOKEN_ICI",  # ← Important
            currency="EUR",
            prices=[types.LabeledPrice(label=item, amount=int(price*100)) for item, qty in cart.items() 
                    for price in [next((p['price'] for cat in products.values() for p in cat if p['name'] == item), 0)] * qty]
        )

    elif call.data == "back_main":
        bot.edit_message_text("👋 **Bonjour et bienvenue !**", chat_id, msg_id, 
                              reply_markup=main_menu(), parse_mode='Markdown')

    bot.answer_callback_query(call.id)

# Gestion du paiement réussi
@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    bot.send_message(message.chat.id, "✅ **Paiement reçu avec succès !**\nVotre commande est en préparation. Merci ! 🎉")
    # Vider le panier après paiement
    carts[message.from_user.id].clear()

# Lancement
print("🤖 Bot démarré avec panier + paiement...")
bot.infinity_polling()
