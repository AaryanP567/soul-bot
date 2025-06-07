import discord
from discord.ext import commands, tasks
import json
import random
import asyncio
from datetime import datetime, timedelta
import os
import uuid

import os
from threading import Thread
from flask import Flask

# Create Flask app for Cloud Run health checks
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return {'status': 'healthy', 'bot': str(bot.user) if bot.user else 'starting'}, 200

@flask_app.route('/health')
def health():
    return {'status': 'ok'}, 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False)

# Start Flask server in background thread
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()

# Bot setup with intents and disabled default help
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Data storage (In production, use a proper database)
user_data = {}
shop_items = {}
daily_missions = {}
tournaments = {}
active_offers = {}  # Store available betting offers
offer_results = {}  # Store completed offer results

# Global economy state
economy_frozen = False

# BLEACH & JOJO themed constants
ZANPAKUTO_NAMES = [
    "Senbonzakura", "Hyorinmaru", "Ryujin Jakka", "Zabimaru", "Wabisuke",
    "Suzumushi", "Benihime", "Shinso", "Kazeshini", "Haineko"
]

STAND_NAMES = [
    "Star Platinum", "The World", "Crazy Diamond", "Gold Experience", 
    "King Crimson", "Silver Chariot", "Magician's Red", "Hermit Purple",
    "Hierophant Green", "Stone Free"
]

SOUL_REAPER_RANKS = [
    "Academy Student", "Unseated Officer", "20th Seat", "15th Seat",
    "10th Seat", "5th Seat", "3rd Seat", "Lieutenant", "Captain", "Captain Commander"
]

# Initialize user data
def init_user(user_id):
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "reiatsu": 5000,  # Main currency (instead of credits)
            "soul_fragments": 0,  # Premium currency
            "zanpakuto": None,
            "stand": None,
            "rank": "Academy Student",
            "level": 1,
            "exp": 0,
            "daily_streak": 0,
            "last_daily": None,
            "last_work": None,
            "last_train": None,
            "inventory": {},
            "active_bets": [],
            "total_winnings": 0,
            "battles_won": 0,
            "achievements": []
        }

# Initialize shop items if not exists
def init_shop():
    global shop_items
    if not shop_items:
        shop_items = {
            'shinigami_robes': {
                'name': '⚔️ Shinigami Robes',
                'description': 'Official Soul Reaper battle attire',
                'price': 2000,
                'currency': 'reiatsu',
                'category': 'equipment',
                'stock': 999,
                'purchasable': True
            },
            'spiritual_amplifier': {
                'name': '💫 Spiritual Pressure Amplifier',
                'description': 'Boost your spiritual energy output',
                'price': 5000,
                'currency': 'reiatsu',
                'category': 'equipment',
                'stock': 999,
                'purchasable': True
            },
            'custom_title': {
                'name': '👑 Custom Title',
                'description': 'Set a personalized title in your profile',
                'price': 3000,
                'currency': 'reiatsu',
                'category': 'cosmetic',
                'stock': 999,
                'purchasable': True
            },
            'hollow_mask': {
                'name': '👹 Hollow Mask Fragment',
                'description': 'Rare fragment with mysterious power',
                'price': 10,
                'currency': 'soul_fragments',
                'category': 'rare',
                'stock': 50,
                'purchasable': True
            },
            'stand_arrow': {
                'name': '🏹 Stand Arrow',
                'description': 'Mystical arrow that awakens Stand powers',
                'price': 75,
                'currency': 'soul_fragments',
                'category': 'rare',
                'stock': 25,
                'purchasable': True
            },
            'hogyoku_shard': {
                'name': '💎 Hogyoku Shard',
                'description': 'Fragment of the legendary evolution orb',
                'price': 50,
                'currency': 'soul_fragments',
                'category': 'rare',
                'stock': 10,
                'purchasable': True
            }
        }

# Save data function
def save_data():
    data_to_save = {
        'user_data': user_data,
        'active_offers': active_offers,
        'offer_results': offer_results,
        'shop_items': shop_items,
        'daily_missions': daily_missions,
        'tournaments': tournaments
    }
    with open('economy_data.json', 'w') as f:
        json.dump(data_to_save, f, indent=2)

# Load data function
def load_data():
    global user_data, active_offers, offer_results, shop_items, daily_missions, tournaments
    try:
        with open('economy_data.json', 'r') as f:
            data = json.load(f)
            user_data = data.get('user_data', {})
            active_offers = data.get('active_offers', {})
            offer_results = data.get('offer_results', {})
            shop_items = data.get('shop_items', {})
            daily_missions = data.get('daily_missions', {})
            tournaments = data.get('tournaments', {})
    except FileNotFoundError:
        user_data = {}
        active_offers = {}
        offer_results = {}
        shop_items = {}
        daily_missions = {}
        tournaments = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has awakened! The Soul Society is now online!')
    load_data()
    init_shop()  # Initialize shop on startup
    daily_reset.start()

@bot.event
async def on_member_join(member):
    init_user(member.id)
    channel = discord.utils.get(member.guild.channels, name='general')
    if channel:
        embed = discord.Embed(
            title="🌟 A New Soul Has Arrived! 🌟",
            description=f"Welcome to the Soul Society, {member.mention}!\n\nYou've been granted **5000 Reiatsu** to begin your journey!\nUse `!profile` to check your spiritual pressure!",
            color=0x00BFFF
        )
        embed.set_footer(text="「This must be the work of an enemy Stand!」")
        await channel.send(embed=embed)

# Help Command - Epic BLEACH x JOJO Style
@bot.command(name='help', aliases=['h', 'commands', 'guide'])
async def help_command(ctx):
    # Create main help embed
    embed = discord.Embed(
        title="⚡ SOUL SOCIETY COMMAND GUIDE ⚡",
        description="*「Welcome to the ultimate spiritual battleground where BLEACH meets JOJO!」*\n\n🔥 **Choose your path, young Soul Reaper!**",
        color=0xFF6B35
    )

    # Profile & Stats Section
    embed.add_field(
        name="📊 **SPIRITUAL STATUS**",
        value=(
            "`!profile` - View your Soul Reaper profile\n"
            "`!balance` - Check your Reiatsu & Soul Fragments\n"
            "`!leaderboard` - See the strongest souls\n"
            "*「Know your power level before challenging others!」*"
        ),
        inline=False
    )

    # Economy Section
    embed.add_field(
        name="💰 **REIATSU GATHERING**",
        value=(
            "`!daily` - Daily spiritual training (24h cooldown)\n"
            "`!work` - Complete Soul Society missions (1h cooldown)\n"
            "`!train` - Intense training for EXP (30m cooldown)\n"
            "*「The path to power requires dedication!」*"
        ),
        inline=False
    )

    # Battle Section
    embed.add_field(
        name="⚔️ **COMBAT SYSTEM**",
        value=(
            "`!battle @user` - Challenge someone to spiritual combat\n"
            "`!give @user amount` - Transfer Reiatsu (5% fee)\n"
            "*「Only through battle can one truly grow stronger!」*"
        ),
        inline=False
    )

    # Betting Section
    embed.add_field(
        name="🎲 **BETTING SYSTEM**",
        value=(
            "`!offers` - View available betting offers\n"
            "`!bet <id> <team> <amount>` - Place a bet\n"
            "`!showbets` - View your active bets\n"
            "`!deletebet <id>` - Cancel a bet\n"
            "`!history` - View completed matches\n"
            "*「Fortune favors the bold!」*"
        ),
        inline=False
    )

    # Shop Section
    embed.add_field(
        name="🏪 **SOUL SOCIETY MARKETPLACE**",
        value=(
            "`!shop` - Browse spiritual items & equipment\n"
            "*「Acquire the tools needed for your journey!」*"
        ),
        inline=False
    )

    # Admin Section (only show if user has admin perms)
    if ctx.author.guild_permissions.administrator:
        embed.add_field(
            name="🛡️ **ADMIN COMMANDS**",
            value=(
                "`!adminhelp` - Complete admin control panel\n"
                "`!newoffer` - Create betting offers\n"
                "`!lockoffer` / `!unlockoffer` - Lock/unlock betting\n"
                "`!result` - End matches & distribute winnings\n"
                "`!additem` / `!edititem` / `!removeitem` - Manage shop\n"
                "`!shopmanage` - Shop management panel\n"
                "*「Control the fate of the Soul Society!」*"
            ),
            inline=False
        )

    # Cool Tips Section
    embed.add_field(
        name="💡 **PRO TIPS**",
        value=(
            "🌟 Keep your daily streak for massive bonuses!\n"
            "⚡ Train regularly to unlock Zanpakuto & Stands\n"
            "🏆 Battle others to climb the power rankings\n"
            "💎 Collect Soul Fragments for premium items\n"
            "🎯 Bet wisely on cricket & football matches!\n"
        ),
        inline=False
    )

    # Footer with cool quotes
    footer_quotes = [
        "「If you want to control your enemy, you must first control yourself.」 - Byakuya",
        "「Your next line is... !daily」 - Joseph Joestar",
        "「Bankai!」 - Every Soul Reaper Ever",
        "「ORAORAORAORAORA!」 - Star Platinum",
        "「The heart may be weak, but bonds make us strong.」 - Sora"
    ]

    embed.set_footer(text=random.choice(footer_quotes))

    # Send main embed
    await ctx.send(embed=embed)

# ===========================================
# GOD MODE ADMIN COMMANDS - ULTIMATE CONTROL
# ===========================================

@bot.command(name='adminhelp', aliases=['godmode', 'admincommands'])
@commands.has_permissions(administrator=True)
async def admin_help(ctx):
    """Complete admin command reference"""
    embed = discord.Embed(
        title="🛡️ GOD MODE ADMIN PANEL 🛡️",
        description="*「With great power comes great responsibility!」*\n\n⚡ **ULTIMATE ADMINISTRATIVE CONTROL** ⚡",
        color=0xFF0000
    )

    embed.add_field(
        name="👤 **USER MANIPULATION**",
        value=(
            "`!setreiatsu @user <amount>` - Set user's Reiatsu\n"
            "`!adreiatsu @user <amount>` - Add/remove Reiatsu\n"
            "`!setfragments @user <amount>` - Set Soul Fragments\n"
            "`!adfragments @user <amount>` - Add/remove Fragments\n"
            "`!setlevel @user <level>` - Set user's level\n"
            "`!setexp @user <exp>` - Set user's EXP\n"
            "`!setrank @user <rank>` - Set user's rank\n"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ **POWER MANIPULATION**",
        value=(
            "`!grantpower @user <zanpakuto/stand> <name>` - Grant powers\n"
            "`!removepower @user <zanpakuto/stand>` - Remove powers\n"
            "`!setstreak @user <days>` - Set daily streak\n"
            "`!resetcooldowns @user` - Reset all cooldowns\n"
            "`!setbattles @user <wins>` - Set battle wins\n"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 **ANALYTICS & MONITORING**",
        value=(
            "`!userinfo @user` - Complete user analysis\n"
            "`!serveranalytics` - Full server economy stats\n"
            "`!richestusers [count]` - Top users by wealth\n"
            "`!activebets` - All active betting positions\n"
            "`!economyreport` - Detailed economy report\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🔧 **BULK OPERATIONS**",
        value=(
            "`!massadd <currency> <amount>` - Give all users currency\n"
            "`!masslevel <levels>` - Level up all users\n"
            "`!resetuser @user` - Complete user reset\n"
            "`!purgedata` - Nuclear option (careful!)\n"
        ),
        inline=False
    )

    embed.add_field(
        name="💰 **ECONOMY CONTROL**",
        value=(
            "`!inflation <percentage>` - Adjust all user wealth\n"
            "`!economyfreeze` - Freeze all transactions\n"
            "`!economyunfreeze` - Unfreeze economy\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🎯 **SPECIAL ADMIN TOOLS**",
        value=(
            "`!impersonate @user <command>` - Run command as user\n"
            "`!backdoor` - Direct database access\n"
            "`!godstats` - Your admin statistics\n"
            "`!emergencybackup` - Create data backup\n"
        ),
        inline=False
    )

    embed.set_footer(text="「You have become the Soul King! Use this power wisely!」")
    await ctx.send(embed=embed)

# ===========================================
# USER MANIPULATION COMMANDS
# ===========================================

@bot.command(name='setreiatsu')
@commands.has_permissions(administrator=True)
async def set_reiatsu(ctx, member: discord.Member, amount: int):
    """Set a user's exact Reiatsu amount"""
    init_user(member.id)
    old_amount = user_data[str(member.id)]['reiatsu']
    user_data[str(member.id)]['reiatsu'] = amount

    embed = discord.Embed(
        title="💰 REIATSU MANIPULATION COMPLETE",
        description=f"**Target:** {member.mention}\n**Old Balance:** {old_amount:,} Reiatsu\n**New Balance:** {amount:,} Reiatsu",
        color=0x00FF00
    )
    embed.add_field(name="👑 Admin", value=ctx.author.mention, inline=True)
    embed.add_field(name="🔄 Change", value=f"{amount - old_amount:+,} Reiatsu", inline=True)
    embed.set_footer(text="「The Soul King has spoken!」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='adreiatsu', aliases=['addreiatsu'])
@commands.has_permissions(administrator=True)
async def add_reiatsu(ctx, member: discord.Member, amount: int):
    """Add or subtract Reiatsu from a user"""
    init_user(member.id)
    old_amount = user_data[str(member.id)]['reiatsu']
    user_data[str(member.id)]['reiatsu'] += amount

    # Prevent negative balance
    if user_data[str(member.id)]['reiatsu'] < 0:
        user_data[str(member.id)]['reiatsu'] = 0

    new_amount = user_data[str(member.id)]['reiatsu']

    embed = discord.Embed(
        title="⚡ REIATSU ADJUSTMENT COMPLETE",
        description=f"**Target:** {member.mention}\n**Adjustment:** {amount:+,} Reiatsu",
        color=0x4169E1
    )
    embed.add_field(name="📊 Before", value=f"{old_amount:,}", inline=True)
    embed.add_field(name="📊 After", value=f"{new_amount:,}", inline=True)
    embed.add_field(name="👑 Admin", value=ctx.author.mention, inline=True)

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='setfragments')
@commands.has_permissions(administrator=True)
async def set_fragments(ctx, member: discord.Member, amount: int):
    """Set a user's exact Soul Fragments amount"""
    init_user(member.id)
    old_amount = user_data[str(member.id)]['soul_fragments']
    user_data[str(member.id)]['soul_fragments'] = amount

    embed = discord.Embed(
        title="💎 SOUL FRAGMENTS MANIPULATION",
        description=f"**Target:** {member.mention}\n**Old:** {old_amount:,} Fragments\n**New:** {amount:,} Fragments",
        color=0x9932CC
    )
    embed.set_footer(text="「Premium currency manipulation complete!」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='adfragments', aliases=['addfragments'])
@commands.has_permissions(administrator=True)
async def add_fragments(ctx, member: discord.Member, amount: int):
    """Add or subtract Soul Fragments from a user"""
    init_user(member.id)
    old_amount = user_data[str(member.id)]['soul_fragments']
    user_data[str(member.id)]['soul_fragments'] += amount

    if user_data[str(member.id)]['soul_fragments'] < 0:
        user_data[str(member.id)]['soul_fragments'] = 0

    new_amount = user_data[str(member.id)]['soul_fragments']

    embed = discord.Embed(
        title="✨ SOUL FRAGMENT ADJUSTMENT",
        description=f"**Target:** {member.mention}\n**Change:** {amount:+,} Fragments",
        color=0xFF69B4
    )
    embed.add_field(name="💎 Before", value=f"{old_amount:,}", inline=True)
    embed.add_field(name="💎 After", value=f"{new_amount:,}", inline=True)

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='setlevel')
@commands.has_permissions(administrator=True)
async def set_level(ctx, member: discord.Member, level: int):
    """Set a user's level directly"""
    if level < 1:
        await ctx.send("「Level must be at least 1!」")
        return

    init_user(member.id)
    old_level = user_data[str(member.id)]['level']
    user_data[str(member.id)]['level'] = level
    user_data[str(member.id)]['exp'] = 0  # Reset EXP when setting level

    # Auto-update rank based on level
    if level >= 50:
        new_rank = "Captain Commander"
    elif level >= 40:
        new_rank = "Captain"
    elif level >= 30:
        new_rank = "Lieutenant"
    elif level >= 20:
        new_rank = "3rd Seat"
    elif level >= 15:
        new_rank = "5th Seat"
    elif level >= 10:
        new_rank = "10th Seat"
    else:
        new_rank = user_data[str(member.id)]['rank']  # Keep current if low level

    user_data[str(member.id)]['rank'] = new_rank

    embed = discord.Embed(
        title="📈 LEVEL MANIPULATION COMPLETE",
        description=f"**Target:** {member.mention}",
        color=0xFF4500
    )
    embed.add_field(name="⬆️ Level Change", value=f"{old_level} → {level}", inline=True)
    embed.add_field(name="🎖️ New Rank", value=new_rank, inline=True)
    embed.add_field(name="👑 Admin", value=ctx.author.mention, inline=True)

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='setexp')
@commands.has_permissions(administrator=True)
async def set_exp(ctx, member: discord.Member, exp: int):
    """Set a user's EXP directly"""
    if exp < 0:
        exp = 0

    init_user(member.id)
    old_exp = user_data[str(member.id)]['exp']
    user_data[str(member.id)]['exp'] = exp

    embed = discord.Embed(
        title="⚡ EXP MANIPULATION COMPLETE",
        description=f"**Target:** {member.mention}\n**EXP:** {old_exp} → {exp}",
        color=0x32CD32
    )
    await ctx.send(embed=embed)
    save_data()

@bot.command(name='setrank')
@commands.has_permissions(administrator=True)
async def set_rank(ctx, member: discord.Member, *, rank):
    """Set a user's rank directly"""
    init_user(member.id)

    if rank not in SOUL_REAPER_RANKS:
        embed = discord.Embed(
            title="❌ Invalid Rank",
            description=f"**Available Ranks:**\n" + "\n".join(f"• {r}" for r in SOUL_REAPER_RANKS),
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    old_rank = user_data[str(member.id)]['rank']
    user_data[str(member.id)]['rank'] = rank

    embed = discord.Embed(
        title="🎖️ RANK MANIPULATION COMPLETE",
        description=f"**Target:** {member.mention}\n**Rank:** {old_rank} → {rank}",
        color=0xFFD700
    )
    await ctx.send(embed=embed)
    save_data()

# ===========================================
# POWER MANIPULATION COMMANDS
# ===========================================

@bot.command(name='grantpower')
@commands.has_permissions(administrator=True)
async def grant_power(ctx, member: discord.Member, power_type, *, power_name):
    """Grant a user a Zanpakuto or Stand"""
    init_user(member.id)

    power_type = power_type.lower()
    if power_type not in ['zanpakuto', 'stand']:
        await ctx.send("「Power type must be 'zanpakuto' or 'stand'!」")
        return

    if power_type == 'zanpakuto':
        if power_name not in ZANPAKUTO_NAMES:
            await ctx.send(f"「Available Zanpakuto: {', '.join(ZANPAKUTO_NAMES)}」")
            return
        user_data[str(member.id)]['zanpakuto'] = power_name
    else:
        if power_name not in STAND_NAMES:
            await ctx.send(f"「Available Stands: {', '.join(STAND_NAMES)}」")
            return
        user_data[str(member.id)]['stand'] = power_name

    embed = discord.Embed(
        title="⚡ POWER GRANTED!",
        description=f"**Target:** {member.mention}\n**Power:** {power_name} ({power_type.title()})",
        color=0xFF0000
    )
    embed.set_footer(text="「A new power awakens!」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='removepower')
@commands.has_permissions(administrator=True)
async def remove_power(ctx, member: discord.Member, power_type):
    """Remove a user's Zanpakuto or Stand"""
    init_user(member.id)

    power_type = power_type.lower()
    if power_type not in ['zanpakuto', 'stand']:
        await ctx.send("「Power type must be 'zanpakuto' or 'stand'!」")
        return

    old_power = user_data[str(member.id)].get(power_type, 'None')
    user_data[str(member.id)][power_type] = None

    embed = discord.Embed(
        title="💀 POWER REMOVED!",
        description=f"**Target:** {member.mention}\n**Removed:** {old_power} ({power_type.title()})",
        color=0x8B0000
    )
    await ctx.send(embed=embed)
    save_data()

@bot.command(name='setstreak')
@commands.has_permissions(administrator=True)
async def set_streak(ctx, member: discord.Member, days: int):
    """Set a user's daily streak"""
    init_user(member.id)
    old_streak = user_data[str(member.id)]['daily_streak']
    user_data[str(member.id)]['daily_streak'] = max(0, days)

    embed = discord.Embed(
        title="🔥 STREAK MANIPULATION",
        description=f"**Target:** {member.mention}\n**Streak:** {old_streak} → {days} days",
        color=0xFF6347
    )
    await ctx.send(embed=embed)
    save_data()

@bot.command(name='resetcooldowns')
@commands.has_permissions(administrator=True)
async def reset_cooldowns(ctx, member: discord.Member):
    """Reset all cooldowns for a user"""
    init_user(member.id)

    user_data[str(member.id)]['last_daily'] = None
    user_data[str(member.id)]['last_work'] = None
    user_data[str(member.id)]['last_train'] = None

    embed = discord.Embed(
        title="⏰ COOLDOWNS RESET",
        description=f"**Target:** {member.mention}\nAll command cooldowns have been cleared!",
        color=0x00CED1
    )
    await ctx.send(embed=embed)
    save_data()

# ===========================================
# ANALYTICS & MONITORING COMMANDS
# ===========================================

@bot.command(name='userinfo', aliases=['inspect'])
@commands.has_permissions(administrator=True)
async def user_info(ctx, member: discord.Member):
    """Complete analysis of a user"""
    init_user(member.id)
    data = user_data[str(member.id)]

    embed = discord.Embed(
        title=f"🔍 COMPLETE USER ANALYSIS",
        description=f"**Target:** {member.mention} (`{member.id}`)",
        color=0x4169E1
    )

    # Basic Stats
    embed.add_field(
        name="💰 **ECONOMY**",
        value=(
            f"**Reiatsu:** {data['reiatsu']:,}\n"
            f"**Soul Fragments:** {data['soul_fragments']:,}\n"
            f"**Total Winnings:** {data['total_winnings']:,}\n"
            f"**Active Bets:** {len(data['active_bets'])}"
        ),
        inline=True
    )

    # Progression
    embed.add_field(
        name="📈 **PROGRESSION**",
        value=(
            f"**Level:** {data['level']}\n"
            f"**EXP:** {data['exp']}/100\n"
            f"**Rank:** {data['rank']}\n"
            f"**Battles Won:** {data['battles_won']}"
        ),
        inline=True
    )

    # Powers & Streaks
    embed.add_field(
        name="⚡ **POWERS & ACTIVITY**",
        value=(
            f"**Zanpakuto:** {data['zanpakuto'] or 'None'}\n"
            f"**Stand:** {data['stand'] or 'None'}\n"
            f"**Daily Streak:** {data['daily_streak']} days\n"
            f"**Battle Power:** {calculate_battle_power(data)}"
        ),
        inline=True
    )

    # Cooldown Status
    now = datetime.now()
    cooldowns = {}

    for cd_type in ['daily', 'work', 'train']:
        last_use = data.get(f'last_{cd_type}')
        if last_use:
            last_time = datetime.fromisoformat(last_use)
            cd_times = {'daily': 86400, 'work': 3600, 'train': 1800}
            time_left = cd_times[cd_type] - (now - last_time).total_seconds()
            cooldowns[cd_type] = "Ready" if time_left <= 0 else f"{int(time_left//60)}m"
        else:
            cooldowns[cd_type] = "Ready"

    embed.add_field(
        name="⏰ **COOLDOWNS**",
        value=(
            f"**Daily:** {cooldowns['daily']}\n"
            f"**Work:** {cooldowns['work']}\n"
            f"**Train:** {cooldowns['train']}"
        ),
        inline=True
    )

    # Recent Activity
    if data['active_bets']:
        bet_info = []
        for bet in data['active_bets'][:3]:  # Show first 3 bets
            bet_info.append(f"• {bet['match_id']}: {bet['amount']:,} on {bet['team']}")

        embed.add_field(
            name="🎲 **ACTIVE BETS**",
            value="\n".join(bet_info) if bet_info else "None",
            inline=True
        )

    # Admin Actions
    embed.add_field(
        name="🛡️ **ADMIN ACTIONS**",
        value=(
            f"`!setreiatsu {member.mention} <amount>`\n"
            f"`!setlevel {member.mention} <level>`\n"
            f"`!resetuser {member.mention}`"
        ),
        inline=False
    )

    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text=f"Account created: {member.created_at.strftime('%Y-%m-%d')}")

    await ctx.send(embed=embed)

@bot.command(name='serveranalytics', aliases=['serverstats'])
@commands.has_permissions(administrator=True)
async def server_analytics(ctx):
    """Complete server economy analysis"""
    total_users = len(user_data)
    total_reiatsu = sum(data['reiatsu'] for data in user_data.values())
    total_fragments = sum(data['soul_fragments'] for data in user_data.values())
    total_active_bets = sum(len(data['active_bets']) for data in user_data.values())

    # Calculate average stats
    avg_reiatsu = total_reiatsu // total_users if total_users > 0 else 0
    avg_level = sum(data['level'] for data in user_data.values()) // total_users if total_users > 0 else 0

    # Count power distribution
    zanpakuto_users = len([d for d in user_data.values() if d['zanpakuto']])
    stand_users = len([d for d in user_data.values() if d['stand']])
    both_powers = len([d for d in user_data.values() if d['zanpakuto'] and d['stand']])

    # Rank distribution
    rank_counts = {}
    for data in user_data.values():
        rank = data['rank']
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    embed = discord.Embed(
        title="📊 SOUL SOCIETY SERVER ANALYTICS",
        description="Complete economic and user analysis",
        color=0x9932CC
    )

    embed.add_field(
        name="👥 **USER STATISTICS**",
        value=(
            f"**Total Users:** {total_users:,}\n"
            f"**Average Level:** {avg_level}\n"
            f"**Zanpakuto Users:** {zanpakuto_users} ({zanpakuto_users/total_users*100:.1f}%)\n"
            f"**Stand Users:** {stand_users} ({stand_users/total_users*100:.1f}%)\n"
            f"**Both Powers:** {both_powers}"
        ),
        inline=True
    )

    embed.add_field(
        name="💰 **ECONOMY OVERVIEW**",
        value=(
            f"**Total Reiatsu:** {total_reiatsu:,}\n"
            f"**Total Fragments:** {total_fragments:,}\n"
            f"**Average Wealth:** {avg_reiatsu:,}\n"
            f"**Active Bets:** {total_active_bets}\n"
            f"**Active Offers:** {len(active_offers)}"
        ),
        inline=True
    )

    embed.add_field(
        name="🎯 **BETTING STATISTICS**",
        value=(
            f"**Total Offers:** {len(active_offers) + len(offer_results)}\n"
            f"**Completed:** {len(offer_results)}\n"
            f"**Active:** {len(active_offers)}\n"
            f"**Shop Items:** {len(shop_items)}"
        ),
        inline=True
    )

    # Top 3 ranks
    top_ranks = sorted(rank_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    rank_text = "\n".join([f"**{rank}:** {count} users" for rank, count in top_ranks])

    embed.add_field(
        name="🏆 **TOP RANKS**",
        value=rank_text,
        inline=False
    )

    embed.set_footer(text="「The Soul Society grows stronger!」")
    await ctx.send(embed=embed)

@bot.command(name='godstats')
@commands.has_permissions(administrator=True)
async def god_stats(ctx):
    """Show admin statistics"""
    embed = discord.Embed(
        title="👑 SOUL KING STATISTICS",
        description=f"**Admin:** {ctx.author.mention}",
        color=0xFFD700
    )

    embed.add_field(
        name="🏰 **DOMAIN CONTROL**",
        value=(
            f"**Total Subjects:** {len(user_data):,}\n"
            f"**Active Offers:** {len(active_offers)}\n"
            f"**Shop Items:** {len(shop_items)}\n"
            f"**Server ID:** {ctx.guild.id}"
        ),
        inline=True
    )

    embed.add_field(
        name="💎 **REALM WEALTH**",
        value=(
            f"**Total Reiatsu:** {sum(d['reiatsu'] for d in user_data.values()):,}\n"
            f"**Total Fragments:** {sum(d['soul_fragments'] for d in user_data.values()):,}\n"
            f"**Economic Activity:** {'🧊 Frozen' if economy_frozen else '🔥 Active'}\n"
            f"**Bot Uptime:** Since last restart"
        ),
        inline=True
    )

    embed.add_field(
        name="🛡️ **ADMIN POWERS**",
        value=(
            "✅ User Manipulation\n"
            "✅ Economy Control\n"
            "✅ Power Granting\n"
            "✅ Data Management\n"
            "✅ God Mode Active"
        ),
        inline=True
    )

    embed.set_footer(text="「You have absolute power over the Soul Society!」")
    await ctx.send(embed=embed)

# ===========================================
# ECONOMY CONTROL COMMANDS
# ===========================================

@bot.command(name='economyfreeze')
@commands.has_permissions(administrator=True)
async def freeze_economy(ctx):
    """Freeze all economic activities"""
    global economy_frozen
    economy_frozen = True

    embed = discord.Embed(
        title="🧊 ECONOMY FROZEN!",
        description="All economic activities have been suspended!\n\n• Daily rewards disabled\n• Work commands disabled\n• Training disabled\n• Betting disabled\n• Shop purchases disabled",
        color=0x87CEEB
    )
    embed.set_footer(text="「Time itself has stopped!」")
    await ctx.send(embed=embed)

@bot.command(name='economyunfreeze')
@commands.has_permissions(administrator=True)
async def unfreeze_economy(ctx):
    """Unfreeze all economic activities"""
    global economy_frozen
    economy_frozen = False

    embed = discord.Embed(
        title="🔥 ECONOMY RESTORED!",
        description="All economic activities have been restored!\n\nThe Soul Society economy is now fully operational.",
        color=0x00FF7F
    )
    embed.set_footer(text="「And time resumes its flow!」")
    await ctx.send(embed=embed)

@bot.command(name='inflation')
@commands.has_permissions(administrator=True)
async def adjust_inflation(ctx, percentage: float):
    """Adjust all user wealth by percentage (inflation/deflation)"""
    if abs(percentage) > 90:
        await ctx.send("「Percentage change too extreme! Use values between -90 and 90.」")
        return

    # Confirmation
    embed = discord.Embed(
        title="⚠️ INFLATION ADJUSTMENT WARNING",
        description=f"You are about to adjust ALL user wealth by **{percentage:+.1f}%**!\n\nThis will affect:\n• All user Reiatsu\n• All user Soul Fragments\n\nReact with ✅ to confirm.",
        color=0xFF6B6B
    )

    message = await ctx.send(embed=embed)
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)

        if str(reaction.emoji) == "❌":
            await ctx.send("「Inflation adjustment cancelled!」")
            return

        # Apply inflation
        multiplier = 1 + (percentage / 100)
        affected_users = 0
        total_reiatsu_change = 0
        total_fragments_change = 0

        for user_id in user_data:
            old_reiatsu = user_data[user_id]['reiatsu']
            old_fragments = user_data[user_id]['soul_fragments']

            user_data[user_id]['reiatsu'] = int(old_reiatsu * multiplier)
            user_data[user_id]['soul_fragments'] = int(old_fragments * multiplier)

            total_reiatsu_change += user_data[user_id]['reiatsu'] - old_reiatsu
            total_fragments_change += user_data[user_id]['soul_fragments'] - old_fragments
            affected_users += 1

        embed = discord.Embed(
            title="📈 INFLATION ADJUSTMENT COMPLETE!",
            description=f"**{percentage:+.1f}%** economic adjustment applied to **{affected_users} users**!",
            color=0x00FF00
        )
        embed.add_field(name="💰 Reiatsu Change", value=f"{total_reiatsu_change:+,}", inline=True)
        embed.add_field(name="💎 Fragment Change", value=f"{total_fragments_change:+,}", inline=True)
        embed.set_footer(text="「You have reshaped the entire economy!」")

        await ctx.send(embed=embed)
        save_data()

    except asyncio.TimeoutError:
        await ctx.send("「Inflation adjustment timed out!」")

# ===========================================
# BULK OPERATIONS
# ===========================================

@bot.command(name='massadd')
@commands.has_permissions(administrator=True)
async def mass_add_currency(ctx, currency, amount: int):
    """Add currency to ALL users"""
    if currency not in ['reiatsu', 'soul_fragments']:
        await ctx.send("「Currency must be 'reiatsu' or 'soul_fragments'!」")
        return

    # Confirmation check
    embed = discord.Embed(
        title="⚠️ MASS OPERATION CONFIRMATION",
        description=f"You are about to give **{amount:+,} {currency.replace('_', ' ').title()}** to **ALL {len(user_data)} users**!\n\nReact with ✅ to confirm or ❌ to cancel.",
        color=0xFF6B6B
    )

    message = await ctx.send(embed=embed)
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)

        if str(reaction.emoji) == "❌":
            await ctx.send("「Mass operation cancelled!」")
            return

        # Execute mass addition
        affected_users = 0
        for user_id in user_data:
            user_data[user_id][currency] += amount
            if user_data[user_id][currency] < 0:
                user_data[user_id][currency] = 0
            affected_users += 1

        embed = discord.Embed(
            title="🌟 MASS OPERATION COMPLETE!",
            description=f"**{amount:+,} {currency.replace('_', ' ').title()}** has been given to **{affected_users} users**!",
            color=0x00FF00
        )
        embed.set_footer(text="「The Soul King's generosity knows no bounds!」")

        await ctx.send(embed=embed)
        save_data()

    except asyncio.TimeoutError:
        await ctx.send("「Mass operation timed out!」")

@bot.command(name='resetuser')
@commands.has_permissions(administrator=True)
async def reset_user(ctx, member: discord.Member):
    """Completely reset a user's data"""

    # Confirmation
    embed = discord.Embed(
        title="⚠️ USER RESET WARNING",
        description=f"You are about to **COMPLETELY RESET** {member.mention}'s data!\n\nThis will:\n• Reset all currencies to starting amounts\n• Remove all powers\n• Reset level to 1\n• Clear all progress\n\nReact with ✅ to confirm.",
        color=0xFF0000
    )

    message = await ctx.send(embed=embed)
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)

        if str(reaction.emoji) == "❌":
            await ctx.send("「User reset cancelled!」")
            return

        # Reset the user
        if str(member.id) in user_data:
            del user_data[str(member.id)]

        init_user(member.id)

        embed = discord.Embed(
            title="🔄 USER RESET COMPLETE",
            description=f"{member.mention} has been completely reset to starting values!",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        save_data()

    except asyncio.TimeoutError:
        await ctx.send("「Reset operation timed out!」")

@bot.command(name='emergencybackup')
@commands.has_permissions(administrator=True)
async def emergency_backup(ctx):
    """Create emergency data backup"""

    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'backup_by': str(ctx.author.id),
        'user_data': user_data,
        'active_offers': active_offers,
        'offer_results': offer_results,
        'shop_items': shop_items
    }

    backup_filename = f"soul_society_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(backup_filename, 'w') as f:
        json.dump(backup_data, f, indent=2)

    embed = discord.Embed(
        title="💾 EMERGENCY BACKUP CREATED",
        description=f"**Backup File:** `{backup_filename}`\n**Created By:** {ctx.author.mention}\n**Users Backed Up:** {len(user_data)}",
        color=0x00BFFF
    )
    embed.set_footer(text="「Your realm data is safely preserved!」")

    await ctx.send(embed=embed)

# ===========================================
# BETTING SYSTEM COMMANDS
# ===========================================

@bot.command(name='newoffer', aliases=['no'])
@commands.has_permissions(administrator=True)
async def new_offer(ctx, match_id, team1, team2, profit_percentage: int):
    """Admin command to create new betting offers with fixed odds"""

    # Validate inputs
    if profit_percentage < 0:
        await ctx.send("「Profit percentage cannot be negative!」")
        return

    if match_id in active_offers:
        await ctx.send(f"「Match ID {match_id} already exists! Choose a different ID.」")
        return

    # Create the offer
    active_offers[match_id] = {
        'id': match_id,
        'team1': team1,
        'team2': team2,
        'profit_percentage': profit_percentage,
        'created_at': datetime.now().isoformat(),
        'bets': {},
        'total_team1_bets': 0,
        'total_team2_bets': 0,
        'total_bets_count': 0,
        'status': 'open'
    }

    # Calculate what users will get for example bet
    example_bet = 500
    example_win = example_bet + (example_bet * profit_percentage // 100)

    embed = discord.Embed(
        title="🏟️ NEW BETTING OFFER CREATED!",
        description=f"**{team1} vs {team2}**\n🎯 Match ID: `{match_id}`\n💰 Profit: {profit_percentage}%",
        color=0x00FF00
    )

    embed.add_field(
        name="📊 Betting Details", 
        value=f"**Example:** Bet {example_bet} → Win {example_win} total\n**Status:** 🟢 Open for betting", 
        inline=False
    )

    embed.add_field(
        name="🎲 How to Bet", 
        value=f"`!bet {match_id} <team1/team2> <amount>`\nExample: `!bet {match_id} {team1} 1000`", 
        inline=False
    )

    embed.set_footer(text="「A new battle begins! Place your bets wisely, Soul Reapers!」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='lockoffer', aliases=['lock', 'lockbet'])
@commands.has_permissions(administrator=True)
async def lock_offer(ctx, match_id):
    """Admin command to lock betting for a specific offer"""
    if match_id not in active_offers:
        await ctx.send("「That offer doesn't exist!」")
        return

    offer_data = active_offers[match_id]

    if offer_data['status'] == 'locked':
        await ctx.send(f"「Offer {match_id} is already locked!」")
        return

    if offer_data['status'] == 'completed':
        await ctx.send(f"「Cannot lock completed offer {match_id}!」")
        return

    # Lock the offer
    offer_data['status'] = 'locked'
    offer_data['locked_at'] = datetime.now().isoformat()

    embed = discord.Embed(
        title="🔒 OFFER LOCKED!",
        description=f"**{offer_data['team1']} vs {offer_data['team2']}**\n\nBetting has been **LOCKED** for this match!",
        color=0xFF6B6B
    )
    embed.add_field(name="🆔 Match ID", value=match_id, inline=True)
    embed.add_field(name="📊 Total Bets", value=f"{offer_data['total_bets_count']}", inline=True)
    embed.add_field(name="💰 Total Pool", value=f"{offer_data['total_team1_bets'] + offer_data['total_team2_bets']:,} Reiatsu", inline=True)
    embed.set_footer(text="「The match has begun! No more bets accepted!」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='unlockoffer', aliases=['unlock', 'unlockbet'])
@commands.has_permissions(administrator=True)
async def unlock_offer(ctx, match_id):
    """Admin command to unlock betting for a specific offer"""
    if match_id not in active_offers:
        await ctx.send("「That offer doesn't exist!」")
        return

    offer_data = active_offers[match_id]

    if offer_data['status'] == 'open':
        await ctx.send(f"「Offer {match_id} is already open for betting!」")
        return

    if offer_data['status'] == 'completed':
        await ctx.send(f"「Cannot unlock completed offer {match_id}!」")
        return

    # Unlock the offer
    offer_data['status'] = 'open'
    if 'locked_at' in offer_data:
        del offer_data['locked_at']

    embed = discord.Embed(
        title="🔓 OFFER UNLOCKED!",
        description=f"**{offer_data['team1']} vs {offer_data['team2']}**\n\nBetting has been **REOPENED** for this match!",
        color=0x00FF7F
    )
    embed.add_field(name="🆔 Match ID", value=match_id, inline=True)
    embed.add_field(name="💰 Profit Rate", value=f"{offer_data['profit_percentage']}%", inline=True)
    embed.add_field(name="🎲 How to Bet", value=f"`!bet {match_id} <team> <amount>`", inline=True)
    embed.set_footer(text="「Betting window reopened! Place your bets quickly!」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='offerstatus', aliases=['status', 'matchstatus'])
@commands.has_permissions(administrator=True)
async def offer_status(ctx, match_id=None):
    """Admin command to check status of offers"""
    if match_id:
        # Check specific offer
        if match_id not in active_offers:
            await ctx.send("「That offer doesn't exist!」")
            return

        offer_data = active_offers[match_id]
        status_emoji = {"open": "🟢", "locked": "🔒", "completed": "✅"}

        embed = discord.Embed(
            title=f"📊 Offer Status: {match_id}",
            description=f"**{offer_data['team1']} vs {offer_data['team2']}**",
            color=0x4169E1
        )
        embed.add_field(name="📈 Status", value=f"{status_emoji.get(offer_data['status'], '❓')} {offer_data['status'].title()}", inline=True)
        embed.add_field(name="💰 Profit Rate", value=f"{offer_data['profit_percentage']}%", inline=True)
        embed.add_field(name="🎲 Total Bets", value=f"{offer_data['total_bets_count']}", inline=True)
        embed.add_field(name="🔵 Team 1 Bets", value=f"{offer_data['total_team1_bets']:,} Reiatsu", inline=True)
        embed.add_field(name="🔴 Team 2 Bets", value=f"{offer_data['total_team2_bets']:,} Reiatsu", inline=True)
        embed.add_field(name="💎 Total Pool", value=f"{offer_data['total_team1_bets'] + offer_data['total_team2_bets']:,} Reiatsu", inline=True)

        if offer_data['status'] == 'locked' and 'locked_at' in offer_data:
            locked_time = datetime.fromisoformat(offer_data['locked_at'])
            embed.add_field(name="🔒 Locked At", value=f"<t:{int(locked_time.timestamp())}:R>", inline=False)

        await ctx.send(embed=embed)
    else:
        # Show all offers status
        if not active_offers:
            await ctx.send("「No active offers to show status for!」")
            return

        embed = discord.Embed(
            title="📊 ALL OFFERS STATUS",
            description="Current status of all active offers:",
            color=0x9932CC
        )

        for offer_id, offer_data in active_offers.items():
            status_emoji = {"open": "🟢", "locked": "🔒", "completed": "✅"}
            status_text = f"{status_emoji.get(offer_data['status'], '❓')} {offer_data['status'].title()}"

            embed.add_field(
                name=f"{offer_data['team1']} vs {offer_data['team2']}",
                value=f"**ID:** {offer_id}\n**Status:** {status_text}\n**Bets:** {offer_data['total_bets_count']}",
                inline=True
            )

        await ctx.send(embed=embed)

@bot.command(name='offers', aliases=['matches', 'games'])
async def view_offers(ctx):
    """View all available offers for betting"""
    if not active_offers:
        embed = discord.Embed(
            title="🏟️ NO ACTIVE OFFERS",
            description="No betting offers available right now!\n\n「Even the strongest warriors need rest...」",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title="🎯 ACTIVE BETTING OFFERS",
        description="Choose your battles wisely, Soul Reaper!",
        color=0x4169E1
    )

    for match_id, offer_data in active_offers.items():
        if offer_data['status'] in ['open', 'locked']:  # Show both open and locked
            example_bet = 1000
            example_win = example_bet + (example_bet * offer_data['profit_percentage'] // 100)

            # Status indicator
            status_text = "🟢 Open for Betting" if offer_data['status'] == 'open' else "🔒 Betting Locked"

            embed.add_field(
                name=f"🏆 {offer_data['team1']} vs {offer_data['team2']}",
                value=(
                    f"🆔 **ID:** `{match_id}`\n"
                    f"📊 **Status:** {status_text}\n"
                    f"💰 **Profit:** {offer_data['profit_percentage']}%\n"
                    f"📈 **Example:** {example_bet} → {example_win}\n"
                    f"🎲 **Total Bets:** {offer_data['total_bets_count']}\n"
                    f"**Team 1 Bets:** {offer_data['total_team1_bets']:,} Reiatsu\n"
                    f"**Team 2 Bets:** {offer_data['total_team2_bets']:,} Reiatsu"
                ),
                inline=False
            )

    embed.set_footer(text="Use !bet <match_id> <team> <amount> to place a bet (if open)")
    await ctx.send(embed=embed)

@bot.command(name='bet')
async def place_bet(ctx, match_id, team_choice, amount: int):
    """Place a bet on an offer"""
    if economy_frozen:
        embed = discord.Embed(
            title="🧊 ECONOMY FROZEN",
            description="All economic activities are currently suspended by the administrators.\n\nPlease wait for the economy to be restored.",
            color=0x87CEEB
        )
        await ctx.send(embed=embed)
        return

    init_user(ctx.author.id)
    user_data_entry = user_data[str(ctx.author.id)]

    # Validate offer exists
    if match_id not in active_offers:
        await ctx.send("「That offer doesn't exist! Use `!offers` to see available offers.」")
        return

    offer_data = active_offers[match_id]

    # Check if offer is locked
    if offer_data['status'] == 'locked':
        embed = discord.Embed(
            title="🔒 BETTING LOCKED!",
            description=f"**{offer_data['team1']} vs {offer_data['team2']}**\n\nThis match is currently **LOCKED**!\nBetting is not allowed at this time.",
            color=0xFF6B6B
        )
        embed.add_field(name="🆔 Match ID", value=match_id, inline=True)
        embed.add_field(name="📊 Status", value="🔒 Locked", inline=True)
        embed.set_footer(text="「The match has begun! Wait for the next opportunity!」")
        await ctx.send(embed=embed)
        return

    # Check if offer is still open
    if offer_data['status'] != 'open':
        await ctx.send("「This offer is no longer accepting bets!」")
        return

    # Validate team choice
    team_choice_lower = team_choice.lower()
    team1_lower = offer_data['team1'].lower()
    team2_lower = offer_data['team2'].lower()

    if team_choice_lower not in ['1', '2', 'team1', 'team2', team1_lower, team2_lower]:
        await ctx.send(f"「Choose team 1 ({offer_data['team1']}) or team 2 ({offer_data['team2']})!\nExample: `!bet {match_id} {offer_data['team1']} {amount}`」")
        return

    # Standardize team choice
    if team_choice_lower in ['1', 'team1', team1_lower]:
        team_choice = 'team1'
        team_name = offer_data['team1']
    else:
        team_choice = 'team2'
        team_name = offer_data['team2']

    # Validate amount
    if amount <= 0:
        await ctx.send("「Bet amount must be positive!」")
        return

    if amount < 100:
        await ctx.send("「Minimum bet amount is 100 Reiatsu!」")
        return

    if user_data_entry['reiatsu'] < amount:
        await ctx.send(f"「You don't have enough Reiatsu! You have {user_data_entry['reiatsu']:,}, need {amount:,}」")
        return

    # Check if user already has a bet on this offer
    user_id = str(ctx.author.id)
    if user_id in offer_data['bets']:
        await ctx.send("「You already have a bet on this offer! Use `!deletebet` to cancel it first.」")
        return

    # Calculate potential winnings with fixed odds
    profit_amount = amount * offer_data['profit_percentage'] // 100
    total_return = amount + profit_amount

    # Place the bet
    user_data_entry['reiatsu'] -= amount
    offer_data['bets'][user_id] = {
        'team': team_choice,
        'amount': amount,
        'potential_return': total_return,
        'user_name': ctx.author.display_name
    }

    # Update offer totals
    if team_choice == 'team1':
        offer_data['total_team1_bets'] += amount
    else:
        offer_data['total_team2_bets'] += amount

    offer_data['total_bets_count'] += 1

    # Add to user's active bets
    user_data_entry['active_bets'].append({
        'match_id': match_id,
        'team': team_choice,
        'amount': amount,
        'potential_return': total_return,
        'match_description': f"{offer_data['team1']} vs {offer_data['team2']}"
    })

    embed = discord.Embed(
        title="🎲 BET PLACED SUCCESSFULLY!",
        description=f"**Match:** {offer_data['team1']} vs {offer_data['team2']}\n**Your Bet:** {amount:,} Reiatsu on {team_name}",
        color=0x00FF7F
    )
    embed.add_field(name="💰 Your Bet", value=f"{amount:,} Reiatsu", inline=True)
    embed.add_field(name="🏆 If You Win", value=f"{total_return:,} Reiatsu", inline=True)
    embed.add_field(name="📈 Profit", value=f"+{profit_amount:,} Reiatsu", inline=True)
    embed.add_field(name="🆔 Match ID", value=match_id, inline=True)
    embed.add_field(name="📊 Profit Rate", value=f"{offer_data['profit_percentage']}%", inline=True)
    embed.add_field(name="👊 Team", value=team_name, inline=True)

    embed.set_footer(text="「Fortune favors the bold! May your spiritual pressure guide you to victory!」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='showbets', aliases=['mybets', 'bets'])
async def show_bets(ctx):
    """Show user's active bets"""
    init_user(ctx.author.id)
    user_data_entry = user_data[str(ctx.author.id)]

    if not user_data_entry['active_bets']:
        embed = discord.Embed(
            title="📋 NO ACTIVE BETS",
            description="You don't have any active bets!\n\n「A warrior who doesn't take risks can't grow stronger!」",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title=f"📋 {ctx.author.display_name}'s Active Bets",
        description="Your current betting positions:",
        color=0x4169E1
    )

    total_bet_amount = 0
    total_potential_return = 0

    for bet in user_data_entry['active_bets']:
        total_bet_amount += bet['amount']
        total_potential_return += bet.get('potential_return', bet['amount'])

        # Get current offer data
        if bet['match_id'] in active_offers:
            offer_data = active_offers[bet['match_id']]
            team_name = offer_data['team1'] if bet['team'] == 'team1' else offer_data['team2']
            profit_amount = bet.get('potential_return', bet['amount']) - bet['amount']

            # Status indicator
            status_text = "🟢 Open" if offer_data['status'] == 'open' else "🔒 Locked"

            embed.add_field(
                name=f"🎯 {bet['match_description']}",
                value=(
                    f"🆔 **ID:** {bet['match_id']}\n"
                    f"📊 **Status:** {status_text}\n"
                    f"👊 **Team:** {team_name}\n"
                    f"💰 **Bet:** {bet['amount']:,} Reiatsu\n"
                    f"🏆 **If Win:** {bet.get('potential_return', bet['amount']):,} Reiatsu\n"
                    f"📈 **Profit:** +{profit_amount:,} Reiatsu"
                ),
                inline=False
            )

    total_potential_profit = total_potential_return - total_bet_amount

    embed.add_field(
        name="📊 BETTING SUMMARY",
        value=(
            f"**Total Bet:** {total_bet_amount:,} Reiatsu\n"
            f"**Potential Return:** {total_potential_return:,} Reiatsu\n"
            f"**Potential Profit:** +{total_potential_profit:,} Reiatsu\n"
            f"**Active Bets:** {len(user_data_entry['active_bets'])}"
        ),
        inline=False
    )
    embed.set_footer(text="「Your fate is in the hands of the spirit world!」")

    await ctx.send(embed=embed)

@bot.command(name='deletebet', aliases=['cancelbet', 'removebet'])
async def delete_bet(ctx, match_id):
    """Cancel a bet before the match starts"""
    init_user(ctx.author.id)
    user_data_entry = user_data[str(ctx.author.id)]
    user_id = str(ctx.author.id)

    # Check if offer exists
    if match_id not in active_offers:
        await ctx.send("「That offer doesn't exist!」")
        return

    offer_data = active_offers[match_id]

    # Check if user has a bet on this offer
    if user_id not in offer_data['bets']:
        await ctx.send("「You don't have a bet on this offer!」")
        return

    # Check if offer is still open
    if offer_data['status'] != 'open':
        await ctx.send("「Cannot cancel bet - match has already started or ended!」")
        return

    # Get bet details
    bet_data = offer_data['bets'][user_id]
    bet_amount = bet_data['amount']
    bet_team = bet_data['team']

    # Remove bet from offer
    del offer_data['bets'][user_id]

    # Update offer totals
    if bet_team == 'team1':
        offer_data['total_team1_bets'] -= bet_amount
    else:
        offer_data['total_team2_bets'] -= bet_amount

    offer_data['total_bets_count'] -= 1

    # Refund user
    user_data_entry['reiatsu'] += bet_amount

    # Remove from user's active bets
    user_data_entry['active_bets'] = [bet for bet in user_data_entry['active_bets'] if bet['match_id'] != match_id]

    embed = discord.Embed(
        title="🔄 BET CANCELLED",
        description=f"Your bet of **{bet_amount:,} Reiatsu** on {offer_data['team1']} vs {offer_data['team2']} has been cancelled and refunded!",
        color=0x00CED1
    )
    embed.set_footer(text="「Sometimes retreat is the wisest strategy!」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='result', aliases=['endoffer', 'r'])
@commands.has_permissions(administrator=True)
async def end_offer(ctx, match_id, winning_team: int):
    """Admin command to end an offer and distribute winnings"""
    if match_id not in active_offers:
        await ctx.send("「Offer not found!」")
        return

    if winning_team not in [1, 2]:
        await ctx.send("「Winning team must be 1 or 2!」")
        return

    offer_data = active_offers[match_id]
    offer_data['status'] = 'completed'
    offer_data['completed_at'] = datetime.now().isoformat()
    offer_data['winning_team'] = winning_team

    winning_team_key = f'team{winning_team}'

    # Calculate and distribute winnings
    winners = []
    losers = []
    total_distributed = 0
    total_lost = 0

    for user_id, bet_data in offer_data['bets'].items():
        if bet_data['team'] == winning_team_key:
            # Winner - give them their return amount
            winnings = bet_data['potential_return']

            if user_id in user_data:
                user_data[user_id]['reiatsu'] += winnings
                user_data[user_id]['total_winnings'] += (winnings - bet_data['amount'])  # Only count profit

                # Remove from active bets
                user_data[user_id]['active_bets'] = [
                    bet for bet in user_data[user_id]['active_bets'] 
                    if bet['match_id'] != match_id
                ]

                winners.append({
                    'name': bet_data['user_name'],
                    'bet': bet_data['amount'],
                    'return': winnings,
                    'profit': winnings - bet_data['amount']
                })
                total_distributed += winnings
        else:
            # Loser - they already lost their bet money
            losers.append({
                'name': bet_data['user_name'],
                'lost': bet_data['amount']
            })
            total_lost += bet_data['amount']

            # Remove from their active bets
            if user_id in user_data:
                user_data[user_id]['active_bets'] = [
                    bet for bet in user_data[user_id]['active_bets'] 
                    if bet['match_id'] != match_id
                ]

    # Create results embed
    embed = discord.Embed(
        title="🏆 MATCH RESULTS",
        description=f"**{offer_data['team1']} vs {offer_data['team2']}**\n🎊 Winner: **{offer_data[f'team{winning_team}']}**",
        color=0xFFD700
    )

    embed.add_field(
        name="📊 Betting Statistics",
        value=(
            f"**Total Bets:** {offer_data['total_bets_count']}\n"
            f"**Winners:** {len(winners)}\n"
            f"**Losers:** {len(losers)}\n"
            f"**Profit Rate:** {offer_data['profit_percentage']}%"
        ),
        inline=True
    )

    embed.add_field(
        name="💰 Financial Summary",
        value=(
            f"**Total Distributed:** {total_distributed:,} Reiatsu\n"
            f"**Total Lost:** {total_lost:,} Reiatsu\n"
            f"**House Edge:** {total_lost - (total_distributed - sum(w['bet'] for w in winners)):,} Reiatsu"
        ),
        inline=True
    )

    if winners:
        winner_text = ""
        for winner in winners[:5]:  # Show top 5 winners
            winner_text += f"🎊 {winner['name']}: {winner['bet']:,} → {winner['return']:,} (+{winner['profit']:,})\n"
        if len(winners) > 5:
            winner_text += f"...and {len(winners) - 5} more!"

        embed.add_field(
            name="🏆 Top Winners",
            value=winner_text,
            inline=False
        )

    embed.set_footer(text="「Victory belongs to those who believe in their power!」")

    # Move to completed offers
    offer_results[match_id] = offer_data
    del active_offers[match_id]

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='history', aliases=['results', 'past'])
async def offer_history(ctx):
    """View completed offer results"""
    if not offer_results:
        embed = discord.Embed(
            title="📚 NO OFFER HISTORY",
            description="No completed offers yet!\n\n「History is written by the victors!」",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title="📚 OFFER HISTORY",
        description="Recent completed betting offers:",
        color=0x9932CC
    )

    # Show last 5 completed offers
    recent_offers = list(offer_results.items())[-5:]

    for match_id, offer_data in recent_offers:
        winning_team_num = offer_data.get('winning_team', 0)
        winner_team = offer_data.get(f'team{winning_team_num}', 'Unknown') if winning_team_num else 'Unknown'
        total_bets = len(offer_data['bets'])

        embed.add_field(
            name=f"🏆 {offer_data['team1']} vs {offer_data['team2']}",
            value=(
                f"🆔 **ID:** {match_id}\n"
                f"🎊 **Winner:** {winner_team}\n"
                f"💰 **Profit Rate:** {offer_data['profit_percentage']}%\n"
                f"🎲 **Total Bets:** {total_bets}"
            ),
            inline=False
        )

    embed.set_footer(text="「Learn from the past to conquer the future!」")
    await ctx.send(embed=embed)

# ===========================================
# SHOP MANAGEMENT SYSTEM
# ===========================================

@bot.command(name='additem', aliases=['newitem'])
@commands.has_permissions(administrator=True)
async def add_shop_item(ctx, item_id, price: int, currency='reiatsu', stock: int = 999, *, name_and_description):
    """Admin command to add new shop item
    Usage: !additem item_id price [currency] [stock] Name | Description
    Example: !additem zanpakuto_boost 15000 reiatsu 100 Zanpakuto Power Boost | Increases Zanpakuto strength by 50%
    """
    init_shop()

    if item_id in shop_items:
        await ctx.send(f"「Item ID '{item_id}' already exists! Use !edititem to modify it.」")
        return

    if '|' not in name_and_description:
        await ctx.send("「Format: !additem <id> <price> [currency] [stock] <name> | <Description>」")
        return

    if currency not in ['reiatsu', 'soul_fragments']:
        await ctx.send("「Currency must be 'reiatsu' or 'soul_fragments'!」")
        return

    if price <= 0 or stock <= 0:
        await ctx.send("「Price and stock must be positive numbers!」")
        return

    name, description = name_and_description.split('|', 1)
    name = name.strip()
    description = description.strip()

    # Add the new item
    shop_items[item_id] = {
        'name': name,
        'description': description,
        'price': price,
        'currency': currency,
        'category': 'custom',
        'stock': stock,
        'purchasable': True,
        'created_by': ctx.author.display_name,
        'created_at': datetime.now().isoformat()
    }

    currency_emoji = "💰" if currency == 'reiatsu' else "💎"

    embed = discord.Embed(
        title="✅ SHOP ITEM ADDED!",
        description=f"New item successfully added to the Soul Society Shop!",
        color=0x00FF7F
    )
    embed.add_field(name="🆔 Item ID", value=item_id, inline=True)
    embed.add_field(name="📛 Name", value=name, inline=True)
    embed.add_field(name="💰 Price", value=f"{currency_emoji} {price:,} {currency.replace('_', ' ').title()}", inline=True)
    embed.add_field(name="📦 Stock", value=f"{stock:,}", inline=True)
    embed.add_field(name="📝 Description", value=description, inline=False)
    embed.set_footer(text=f"Created by {ctx.author.display_name}")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='removeitem', aliases=['deleteitem'])
@commands.has_permissions(administrator=True)
async def remove_shop_item(ctx, item_id):
    """Admin command to remove shop item"""
    init_shop()

    if item_id not in shop_items:
        await ctx.send(f"「Item ID '{item_id}' doesn't exist!」")
        return

    item_data = shop_items[item_id]
    del shop_items[item_id]

    embed = discord.Embed(
        title="🗑️ SHOP ITEM REMOVED!",
        description=f"**{item_data['name']}** has been removed from the shop!",
        color=0xFF6B6B
    )
    embed.add_field(name="🆔 Removed ID", value=item_id, inline=True)
    embed.add_field(name="💰 Was Priced", value=f"{item_data['price']:,} {item_data['currency'].replace('_', ' ').title()}", inline=True)
    embed.set_footer(text="「Another soul returns to the void...」")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='edititem', aliases=['modifyitem'])
@commands.has_permissions(administrator=True)
async def edit_shop_item(ctx, item_id, field, *, new_value):
    """Admin command to edit shop item
    Usage: !edititem <item_id> <field> <new_value>
    Fields: name, description, price, currency, stock, purchasable
    Example: !edititem zanpakuto_boost price 20000
    """
    init_shop()

    if item_id not in shop_items:
        await ctx.send(f"「Item ID '{item_id}' doesn't exist!」")
        return

    valid_fields = ['name', 'description', 'price', 'currency', 'stock', 'purchasable']
    if field not in valid_fields:
        await ctx.send(f"「Valid fields: {', '.join(valid_fields)}」")
        return

    item_data = shop_items[item_id]
    old_value = item_data[field]

    # Type conversion for specific fields
    if field == 'price' or field == 'stock':
        try:
            new_value = int(new_value)
            if new_value <= 0:
                await ctx.send("「Price and stock must be positive numbers!」")
                return
        except ValueError:
            await ctx.send(f"「{field.title()} must be a number!」")
            return
    elif field == 'currency':
        if new_value not in ['reiatsu', 'soul_fragments']:
            await ctx.send("「Currency must be 'reiatsu' or 'soul_fragments'!」")
            return
    elif field == 'purchasable':
        new_value = new_value.lower() in ['true', 'yes', '1', 'on', 'enable']

    # Update the field
    item_data[field] = new_value
    item_data['last_edited'] = datetime.now().isoformat()
    item_data['last_edited_by'] = ctx.author.display_name

    embed = discord.Embed(
        title="✏️ SHOP ITEM EDITED!",
        description=f"**{item_data['name']}** has been updated!",
        color=0x00BFFF
    )
    embed.add_field(name="🆔 Item ID", value=item_id, inline=True)
    embed.add_field(name="📝 Field", value=field.title(), inline=True)
    embed.add_field(name="🔄 Change", value=f"{old_value} → {new_value}", inline=True)
    embed.set_footer(text=f"Edited by {ctx.author.display_name}")

    await ctx.send(embed=embed)
    save_data()

@bot.command(name='shopmanage', aliases=['manageshop', 'shopinfo'])
@commands.has_permissions(administrator=True)
async def shop_management(ctx):
    """Admin command to view shop management info"""
    init_shop()

    embed = discord.Embed(
        title="🛠️ SHOP MANAGEMENT PANEL",
        description="Admin tools for managing the Soul Society Shop",
        color=0x9932CC
    )

    embed.add_field(
        name="➕ Add New Item",
        value="`!additem <id> <price> [currency] [stock] <name> | <Description>`",
        inline=False
    )

    embed.add_field(
        name="✏️ Edit Existing Item",
        value="`!edititem <id> <field> <new_value>`\nFields: name, description, price, currency, stock, purchasable",
        inline=False
    )

    embed.add_field(
        name="🗑️ Remove Item",
        value="`!removeitem <id>`",
        inline=False
    )

    embed.add_field(
        name="📊 Current Shop Stats",
        value=f"**Total Items:** {len(shop_items)}\n**Available:** {len([i for i in shop_items.values() if i['purchasable']])}\n**Out of Stock:** {len([i for i in shop_items.values() if i['stock'] <= 0])}",
        inline=False
    )

    # Show current items
    if shop_items:
        items_text = ""
        for item_id, item_data in list(shop_items.items())[:5]:  # Show first 5
            status = "✅" if item_data['purchasable'] and item_data['stock'] > 0 else "❌"
            currency_emoji = "💰" if item_data['currency'] == 'reiatsu' else "💎"
            items_text += f"{status} `{item_id}` - {currency_emoji}{item_data['price']:,} ({item_data['stock']} left)\n"

        if len(shop_items) > 5:
            items_text += f"...and {len(shop_items) - 5} more items"

        embed.add_field(
            name="🏪 Current Items",
            value=items_text,
            inline=False
        )

    embed.set_footer(text="「Control the economy of the Soul Society!」")
    await ctx.send(embed=embed)

# ===========================================
# CORE ECONOMY COMMANDS
# ===========================================

@bot.command(name='profile', aliases=['p', 'stats'])
async def profile(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    init_user(member.id)
    data = user_data[str(member.id)]

    embed = discord.Embed(
        title=f"📋 {member.display_name}'s Soul Profile",
        color=0xFF6B35
    )

    embed.add_field(
        name="💫 Reiatsu (Spiritual Pressure)", 
        value=f"{data['reiatsu']:,}", 
        inline=True
    )
    embed.add_field(
        name="👻 Soul Fragments", 
        value=f"{data['soul_fragments']:,}", 
        inline=True
    )
    embed.add_field(
        name="🎖️ Soul Reaper Rank", 
        value=data['rank'], 
        inline=True
    )

    embed.add_field(
        name="⚡ Level", 
        value=f"{data['level']} ({data['exp']}/100 EXP)", 
        inline=True
    )
    embed.add_field(
        name="🔥 Daily Streak", 
        value=f"{data['daily_streak']} days", 
        inline=True
    )
    embed.add_field(
        name="⚔️ Battles Won", 
        value=f"{data['battles_won']}", 
        inline=True
    )

    if data['zanpakuto']:
        embed.add_field(name="⚔️ Zanpakuto", value=data['zanpakuto'], inline=True)
    if data['stand']:
        embed.add_field(name="👊 Stand", value=data['stand'], inline=True)

    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text="「Yare yare daze...」")

    await ctx.send(embed=embed)

@bot.command(name='balance', aliases=['bal', 'reiatsu'])
async def balance(ctx):
    init_user(ctx.author.id)
    data = user_data[str(ctx.author.id)]

    embed = discord.Embed(
        title="💰 Your Spiritual Wealth",
        description=f"**Reiatsu:** {data['reiatsu']:,}\n**Soul Fragments:** {data['soul_fragments']:,}",
        color=0x4169E1
    )
    embed.set_footer(text="「I'll use my Stand to protect these riches!」")
    await ctx.send(embed=embed)

@bot.command(name='daily')
async def daily_reward(ctx):
    if economy_frozen:
        embed = discord.Embed(
            title="🧊 ECONOMY FROZEN",
            description="All economic activities are currently suspended by the administrators.\n\nPlease wait for the economy to be restored.",
            color=0x87CEEB
        )
        await ctx.send(embed=embed)
        return

    init_user(ctx.author.id)
    data = user_data[str(ctx.author.id)]

    now = datetime.now()
    last_daily = datetime.fromisoformat(data['last_daily']) if data['last_daily'] else None

    if last_daily and (now - last_daily).total_seconds() < 86400:  # 24 hours
        time_left = 86400 - (now - last_daily).total_seconds()
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)

        embed = discord.Embed(
            title="⏰ Daily Reward Already Claimed!",
            description=f"Come back in {hours}h {minutes}m for your next daily reward!",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    # Calculate streak
    if last_daily and (now - last_daily).total_seconds() <= 172800:  # Within 48 hours
        data['daily_streak'] += 1
    else:
        data['daily_streak'] = 1

    # Calculate reward based on streak
    base_reward = 500
    streak_bonus = min(data['daily_streak'] * 50, 1000)  # Max 1000 bonus
    total_reward = base_reward + streak_bonus

    # Chance for soul fragments
    soul_fragments = 0
    if random.random() < 0.1:  # 10% chance
        soul_fragments = random.randint(1, 5)
        data['soul_fragments'] += soul_fragments

    data['reiatsu'] += total_reward
    data['last_daily'] = now.isoformat()
    data['exp'] += 10

    embed = discord.Embed(
        title="🎁 Daily Spiritual Training Complete!",
        description=f"You've gained **{total_reward:,} Reiatsu**!\n{'🌟 Bonus: ' + str(soul_fragments) + ' Soul Fragments!' if soul_fragments else ''}",
        color=0x00FF7F
    )
    embed.add_field(
        name="🔥 Streak Bonus", 
        value=f"Day {data['daily_streak']} (+{streak_bonus} Reiatsu)", 
        inline=False
    )
    embed.set_footer(text="「The power of friendship gives me strength!」")

    await ctx.send(embed=embed)
    check_level_up(ctx.author.id)
    save_data()

@bot.command(name='work')
async def work(ctx):
    if economy_frozen:
        embed = discord.Embed(
            title="🧊 ECONOMY FROZEN",
            description="All economic activities are currently suspended by the administrators.\n\nPlease wait for the economy to be restored.",
            color=0x87CEEB
        )
        await ctx.send(embed=embed)
        return

    init_user(ctx.author.id)
    data = user_data[str(ctx.author.id)]

    now = datetime.now()
    last_work = datetime.fromisoformat(data['last_work']) if data['last_work'] else None

    if last_work and (now - last_work).total_seconds() < 3600:  # 1 hour cooldown
        time_left = 3600 - (now - last_work).total_seconds()
        minutes = int(time_left // 60)

        embed = discord.Embed(
            title="⏰ Still Recovering from Last Mission!",
            description=f"Wait {minutes} more minutes before your next mission!",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    # Different work scenarios based on rank
    work_scenarios = {
        "Academy Student": [
            ("Cleaned the Academy grounds", 150, 200),
            ("Helped in the library", 100, 180),
            ("Sparred with fellow students", 120, 220)
        ],
        "Lieutenant": [
            ("Led a patrol mission", 300, 500),
            ("Trained new recruits", 250, 400),
            ("Investigated Hollow activity", 350, 600)
        ],
        "Captain": [
            ("Attended Captain's meeting", 500, 800),
            ("Defeated a powerful Hollow", 600, 1000),
            ("Protected Karakura Town", 700, 1200)
        ]
    }

    scenarios = work_scenarios.get(data['rank'], work_scenarios["Academy Student"])
    scenario, min_reward, max_reward = random.choice(scenarios)
    reward = random.randint(min_reward, max_reward)

    data['reiatsu'] += reward
    data['last_work'] = now.isoformat()
    data['exp'] += 5

    embed = discord.Embed(
        title="💼 Mission Complete!",
        description=f"**{scenario}**\n\nYou earned **{reward:+,} Reiatsu**!",
        color=0x32CD32
    )
    embed.set_footer(text="「MUDA MUDA MUDA!」")

    await ctx.send(embed=embed)
    check_level_up(ctx.author.id)
    save_data()

@bot.command(name='train', aliases=['t'])
async def train(ctx):
    if economy_frozen:
        embed = discord.Embed(
            title="🧊 ECONOMY FROZEN",
            description="All economic activities are currently suspended by the administrators.\n\nPlease wait for the economy to be restored.",
            color=0x87CEEB
        )
        await ctx.send(embed=embed)
        return

    init_user(ctx.author.id)
    data = user_data[str(ctx.author.id)]

    now = datetime.now()
    last_train = datetime.fromisoformat(data['last_train']) if data['last_train'] else None

    if last_train and (now - last_train).total_seconds() < 1800:  # 30 min cooldown
        time_left = 1800 - (now - last_train).total_seconds()
        minutes = int(time_left // 60)

        embed = discord.Embed(
            title="😤 Still Exhausted from Training!",
            description=f"Rest for {minutes} more minutes!",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    training_types = [
        ("Bankai meditation", 20, 30),
        ("Hollow combat practice", 15, 25),
        ("Shunpo speed training", 18, 28),
        ("Stand ability development", 22, 32),
        ("Hamon breathing technique", 16, 26)
    ]

    training, min_exp, max_exp = random.choice(training_types)
    exp_gained = random.randint(min_exp, max_exp)

    # Small chance for rare rewards
    bonus_reward = ""
    if random.random() < 0.05:  # 5% chance
        if not data['zanpakuto'] and random.random() < 0.5:
            data['zanpakuto'] = random.choice(ZANPAKUTO_NAMES)
            bonus_reward = f"\n🎊 **You've awakened your Zanpakuto: {data['zanpakuto']}!**"
        elif not data['stand'] and random.random() < 0.5:
            data['stand'] = random.choice(STAND_NAMES)
            bonus_reward = f"\n🎊 **You've manifested your Stand: {data['stand']}!**"

    data['exp'] += exp_gained
    data['last_train'] = now.isoformat()

    embed = discord.Embed(
        title="🏋️ Training Session Complete!",
        description=f"**{training}**\n\nGained **{exp_gained} EXP**!{bonus_reward}",
        color=0xFF4500
    )
    embed.set_footer(text="「My resolve is unshakeable!」")

    await ctx.send(embed=embed)
    check_level_up(ctx.author.id)
    save_data()

@bot.command(name='battle', aliases=['fight', 'duel'])
async def battle(ctx, opponent: discord.Member = None):
    if opponent is None or opponent.bot or opponent == ctx.author:
        await ctx.send("「You need a worthy opponent to battle!」")
        return

    init_user(ctx.author.id)
    init_user(opponent.id)

    challenger_data = user_data[str(ctx.author.id)]
    opponent_data = user_data[str(opponent.id)]

    # Check if both players have enough reiatsu to bet
    min_bet = 100
    if challenger_data['reiatsu'] < min_bet or opponent_data['reiatsu'] < min_bet:
        await ctx.send(f"Both fighters need at least {min_bet} Reiatsu to battle!")
        return

    # Create battle embed
    embed = discord.Embed(
        title="⚔️ BATTLE CHALLENGE!",
        description=f"{ctx.author.mention} has challenged {opponent.mention} to a spiritual battle!\n\n{opponent.mention}, react with ⚔️ to accept or ❌ to decline!",
        color=0xFF0000
    )
    embed.set_footer(text="Battle expires in 60 seconds")

    message = await ctx.send(embed=embed)
    await message.add_reaction("⚔️")
    await message.add_reaction("❌")

    def check(reaction, user):
        return user == opponent and str(reaction.emoji) in ["⚔️", "❌"] and reaction.message.id == message.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)

        if str(reaction.emoji) == "❌":
            await ctx.send(f"{opponent.mention} declined the battle! 「What a coward!」")
            return

        # Battle mechanics
        challenger_power = calculate_battle_power(challenger_data)
        opponent_power = calculate_battle_power(opponent_data)

        # Add some randomness
        challenger_roll = random.randint(1, 100)
        opponent_roll = random.randint(1, 100)

        challenger_total = challenger_power + challenger_roll
        opponent_total = opponent_power + opponent_roll

        # Determine winner
        if challenger_total > opponent_total:
            winner = ctx.author
            loser = opponent
            winner_data = challenger_data
            loser_data = opponent_data
            winner_total = challenger_total
            loser_total = opponent_total
        else:
            winner = opponent
            loser = ctx.author
            winner_data = opponent_data
            loser_data = challenger_data
            winner_total = opponent_total
            loser_total = challenger_total

        # Calculate rewards/losses
        bet_amount = min(winner_data['reiatsu'], loser_data['reiatsu']) // 10  # 10% of lower balance
        bet_amount = max(bet_amount, min_bet)

        winner_data['reiatsu'] += bet_amount
        loser_data['reiatsu'] -= bet_amount
        winner_data['battles_won'] += 1
        winner_data['exp'] += 25
        loser_data['exp'] += 10  # Consolation exp

        # Battle result embed
        result_embed = discord.Embed(
            title="⚔️ BATTLE RESULTS!",
            color=0x00FF00
        )
        result_embed.add_field(
            name="🏆 WINNER",
            value=f"{winner.mention}\nPower: {winner_total}",
            inline=True
        )
        result_embed.add_field(
            name="💀 DEFEATED",
            value=f"{loser.mention}\nPower: {loser_total}",
            inline=True
        )
        result_embed.add_field(
            name="💰 Reiatsu Transfer",
            value=f"{bet_amount:,} Reiatsu",
            inline=True
        )
        result_embed.set_footer(text="「The strong survive, the weak perish!」")

        await ctx.send(embed=result_embed)
        check_level_up(winner.id)
        save_data()

    except asyncio.TimeoutError:
        await ctx.send("Battle challenge expired! 「Too slow!」")

def calculate_battle_power(data):
    base_power = data['level'] * 10
    rank_bonus = SOUL_REAPER_RANKS.index(data['rank']) * 5
    zanpakuto_bonus = 20 if data['zanpakuto'] else 0
    stand_bonus = 25 if data['stand'] else 0
    return base_power + rank_bonus + zanpakuto_bonus + stand_bonus

def check_level_up(user_id):
    data = user_data[str(user_id)]
    if data['exp'] >= 100:
        data['level'] += 1
        data['exp'] = 0

        # Rank promotion logic
        if data['level'] >= 10 and data['rank'] == "Academy Student":
            data['rank'] = "Unseated Officer"
        elif data['level'] >= 20 and data['rank'] == "Unseated Officer":
            data['rank'] = "20th Seat"
        # Add more rank progression logic

        return True
    return False

@bot.command(name='shop')
async def shop(ctx):
    init_shop()

    if not shop_items:
        embed = discord.Embed(
            title="🏪 Soul Society Shop",
            description="The shop is currently empty!\n\n「Even the Soul Society needs time to restock...」",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title="🏪 Soul Society Shop",
        description="Purchase items with your Reiatsu or Soul Fragments!",
        color=0x9932CC
    )

    # Group items by category
    categories = {}
    for item_id, item_data in shop_items.items():
        if not item_data['purchasable']:
            continue

        category = item_data.get('category', 'misc').title()
        if category not in categories:
            categories[category] = []

        currency_emoji = "💰" if item_data['currency'] == 'reiatsu' else "💎"
        stock_text = f" (Stock: {item_data['stock']})" if item_data['stock'] < 999 else ""

        categories[category].append(
            f"• {item_data['name']} - {currency_emoji}{item_data['price']:,} {item_data['currency'].replace('_', ' ').title()}{stock_text}"
        )

    # Add categories to embed
    category_emojis = {
        'Equipment': '⚔️',
        'Cosmetic': '🎭',
        'Rare': '💎',
        'Custom': '✨',
        'Misc': '📦'
    }

    for category, items in categories.items():
        emoji = category_emojis.get(category, '📦')
        embed.add_field(
            name=f"{emoji} {category}",
            value="\n".join(items),
            inline=False
        )

    embed.set_footer(text="Use !buy <item_id> to purchase | 「Money can't buy everything, but it helps!」")
    await ctx.send(embed=embed)

@bot.command(name='leaderboard', aliases=['lb', 'top'])
async def leaderboard(ctx):
    # Sort users by reiatsu
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['reiatsu'], reverse=True)[:10]

    embed = discord.Embed(
        title="🏆 Soul Society Leaderboard",
        description="Top 10 Strongest Souls",
        color=0xFFD700
    )

    medals = ["🥇", "🥈", "🥉"] + ["🎖️"] * 7

    for i, (user_id, data) in enumerate(sorted_users):
        try:
            user = bot.get_user(int(user_id))
            if user:
                embed.add_field(
                    name=f"{medals[i]} #{i+1} {user.display_name}",
                    value=f"Reiatsu: {data['reiatsu']:,}\nRank: {data['rank']}\nLevel: {data['level']}",
                    inline=True
                )
        except:
            continue

    embed.set_footer(text="「Only the strongest reach the top!」")
    await ctx.send(embed=embed)

@bot.command(name='give', aliases=['transfer', 'send'])
async def give_reiatsu(ctx, member: discord.Member, amount: int):
    if member.bot or member == ctx.author:
        await ctx.send("「You cannot transfer to bots or yourself!」")
        return

    if amount <= 0:
        await ctx.send("「Amount must be positive!」")
        return

    init_user(ctx.author.id)
    init_user(member.id)

    sender_data = user_data[str(ctx.author.id)]
    receiver_data = user_data[str(member.id)]

    if sender_data['reiatsu'] < amount:
        await ctx.send("「You don't have enough Reiatsu!」")
        return

    # Transfer with small fee
    fee = max(1, amount // 20)  # 5% fee
    transfer_amount = amount - fee

    sender_data['reiatsu'] -= amount
    receiver_data['reiatsu'] += transfer_amount

    embed = discord.Embed(
        title="💸 Reiatsu Transfer Complete!",
        description=f"{ctx.author.mention} sent **{transfer_amount:,} Reiatsu** to {member.mention}\n\n*Transfer fee: {fee:,} Reiatsu*",
        color=0x00CED1
    )
    embed.set_footer(text="「Generosity is the mark of a true warrior!」")

    await ctx.send(embed=embed)
    save_data()

# Background task for daily resets
@tasks.loop(hours=24)
async def daily_reset():
    # Reset daily missions, update shop, etc.
    pass

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="⏰ Command on Cooldown",
            description=f"Try again in {round(error.retry_after, 2)} seconds!",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("「You're missing required arguments! Check the command usage.」")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("「You don't have permission to use this command!」")
    else:
        print(f"Error: {error}")

# Run the bot
if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
