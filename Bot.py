import telebot
from telebot import types
from collections import defaultdict
import os

# ==================== CONFIG RAILWAY ====================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PAYPAL_USERNAME = os.getenv("PAYPAL_USERNAME")  # Ex: tonnompaypal

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN non défini !")
if not PAYPAL_USERNAME:
    raise ValueError("❌ PAYPAL_USERNAME non défini ! (ex: tonnompaypal)")

bot = telebot.TeleBot(TOKEN)

# Panier (garde l'ancien système)
carts = defaultdict(dict)

# ==================== PRODUITS (inchangé) ====================
products = {
    "otacos": [{"name": "Tacos Classique", "price": 8.90}, {"name": "Tacos Poulet", "price": 9.90}, {"name": "Frites", "price": 3.50}],
    "pizzatime": [{"name": "Margherita", "price": 10.90}, {"name": "Pepperoni", "price": 12.90}, {"name": "Boisson", "price": 2.50}],
    "chamas": [{"name": "Burrito Boeuf", "price": 9.50}, {"name": "Quesadilla", "price": 8.90}],
    "pitaya": [{"name": "Açaï Bowl", "price": 7.90}, {"name": "Smoothie", "price": 5.90}],
    "divers": [{"name": "Hot Dog", "price": 4.50}, {"name": "Croissant", "price": 2.20}],
    "traidinn": [{"name": "Burger Classique", "price": 11.90}, {"name": "Chicken Burger", "price": 10.90}]
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

# (Les autres fonctions category_menu, cart_text restent identiques → je les garde courtes ici)
def category_menu(category):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, p in enumerate(products.get(category, [])):
        markup.add(types.InlineKeyboardButton(f"{p['name']} — {p['price']}€", callback_data=f"add_{category}_{i}"))
    markup.add(types.InlineKeyboardButton("🛍 Voir mon panier", callback_data="view_cart"))
    markup.add(types.InlineKeyboardButton("🔙 Retour Produits", callback_data="menu_produits"))
    return markup

def cart_text(user_id):
    cart = carts[user_id]
    if not cart:
        return "Votre panier est vide 🛒"
    total = sum(next((p['price'] for cat in products.values() for p in cat if p['name'] == item), 0) * qty for item, qty in cart.items())
    lines = ["🛍 **Votre Panier**\n"] + [f"{qty}x {item} → {next((p['price'] for cat in products.values() for p in cat if p['name'] == item), 0)*qty:.2f}€" for item, qty in cart.items()]
    lines.append(f"\n**Total : {total:.2f}€**")
    return "\n".join(lines)

# ==================== START (CORRIGÉ) ====================
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
        bot.edit_message_text("🛒 **Nos Produits**\nChoisissez votre enseigne :", chat_id, msg_id, reply_markup=produits_menu(), parse_mode='Markdown')

    elif call.data == "menu_recharger":
        recharger_menu = types.InlineKeyboardMarkup(row_width=2)
        recharger_menu.add(
            types.InlineKeyboardButton("10 €", callback_data="recharge_10"),
            types.InlineKeyboardButton("20 €", callback_data="recharge_20"),
            types.InlineKeyboardButton("50 €", callback_data="recharge_50"),
            types.InlineKeyboardButton("Autre montant", callback_data="recharge_custom")
        )
        recharger_menu.add(types.InlineKeyboardButton("🔙 Retour", callback_data="back_main"))
        bot.edit_message_text("💰 **Recharger votre solde**\nChoisissez un montant :", chat_id, msg_id, reply_markup=recharger_menu, parse_mode='Markdown')

    elif call.data.startswith("recharge_"):
        if call.data == "recharge_custom":
            bot.answer_callback_query(call.id, "Utilisez /recharger 25 pour un montant personnalisé")
            return
        amount = int(call.data.split("_")[1])
        link = f"https://paypal.me/{PAYPAL_USERNAME}/{amount}EUR"
        bot.send_message(chat_id, f"💰 **Recharge de {amount}€**\n\nClique sur le lien pour payer via PayPal :\n\n{link}")
        bot.answer_callback_query(call.id, "Lien PayPal envoyé !")

    # === Panier et produits (inchangé) ===
    elif call.data.startswith("cat_"):
        cat = call.data[4:]
        bot.edit_message_text(f"📋 **{cat.replace('_', ' ').title()}**", chat_id, msg_id, reply_markup=category_menu(cat), parse_mode='Markdown')

    elif call.data.startswith("add_"):
        _, cat, idx = call.data.split("_")
        idx = int(idx)
        product = products[cat][idx]
        name = product["name"]
        carts[user_id][name] = carts[user_id].get(name, 0) + 1
        bot.answer_callback_query(call.id, f"✅ {name} ajouté !")

    elif call.data == "view_cart":
        text = cart_text(user_id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("✅ Commander (Panier)", callback_data="checkout"))
        markup.add(types.InlineKeyboardButton("🗑 Vider", callback_data="clear_cart"))
        markup.add(types.InlineKeyboardButton("🔙 Continuer", callback_data="menu_produits"))
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode='Markdown')

    elif call.data == "clear_cart":
        carts[user_id].clear()
        bot.answer_callback_query(call.id, "Panier vidé")
        bot.edit_message_text(cart_text(user_id), chat_id, msg_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Retour", callback_data="menu_produits")), parse_mode='Markdown')

    elif call.data == "checkout":
        # Pour l'instant on redirige vers recharger (tu peux améliorer plus tard)
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "Pour payer la commande, utilise le menu **Recharger** ou /recharger", reply_markup=main_menu())

    elif call.data == "back_main":
        bot.edit_message_text("👋 **Bonjour et bienvenue !**", chat_id, msg_id, reply_markup=main_menu(), parse_mode='Markdown')

    bot.answer_callback_query(call.id)

# Commande manuelle pour montant personnalisé
@bot.message_handler(commands=['recharger'])
def recharge_custom(message):
    try:
        amount = float(message.text.split()[1])
        link = f"https://paypal.me/{PAYPAL_USERNAME}/{amount}EUR"
        bot.send_message(message.chat.id, f"💰 **Recharge de {amount}€**\n\nPayez ici :\n{link}")
    except:
        bot.send_message(message.chat.id, "Utilisation : `/recharger 25` (pour 25€)")

# Lancement
if __name__ == "__main__":
    print("🤖 Bot démarré avec succès sur Railway !")
    bot.infinity_polling()
