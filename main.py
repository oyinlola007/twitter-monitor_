import sqlite3, asyncio, os, time, requests, json
import discord
from operator import itemgetter

import cogs.config as config
import cogs.strings as strings
import cogs.db as db
import cogs.twitter_methods as tweepy

db.initializeDB()

client = discord.Client()

@client.event
async def on_ready():
    print(strings.LOGGED_IN.format(client.user))


@client.event
async def on_message(message):
    if message.content.lower().startswith(db.get_command("adduser")):
        try:
            screen_name = message.content.split()[1].strip("@")
            try:
                id = await tweepy.get_id(screen_name)
                try:
                    db.insert_monitoring(id, screen_name)
                    await message.channel.send(strings.MONITOR_ADDED)
                except:
                    try:
                        db.update_monitoring(screen_name, "1")
                        await message.channel.send(strings.MONITOR_ADDED)
                    except:
                        await message.channel.send(strings.ALREADY_MONITORED)
            except Exception as e:
                db.insert_pending(screen_name, str(message.author.id))
                await message.channel.send(strings.MONITOR_ADDED)
        except:
            await message.channel.send(strings.WRONG_FORMAT)

    elif message.content.lower().startswith(db.get_command("getusers")):
        users = ""
        cursor = db.get_all_monitoring()
        for row in cursor:
            users += f"\n@{row[1]}"

        if users == "":
            await message.channel.send(strings.USER_NON)
        else:
            await message.channel.send(f">>> {users.strip()}")

    elif message.content.lower().startswith(db.get_command("removeuser")):
        try:
            screen_name = message.content.split()[1].strip("@")
            try:
                db.update_untracked_id(db.get_monitoring_id(screen_name), "0")
                db.update_monitoring(screen_name, "0")
                await message.channel.send(strings.USER_SUCCESSFULLY_REMOVED)
            except:
                await message.channel.send(strings.USER_NOT_IN_DB)
        except:
            await message.channel.send(strings.WRONG_FORMAT)

    elif message.content.lower().startswith(db.get_command("search")):
        try:
            duration = message.content.split()[2].strip("@")
            screen_name = message.content.split()[1].strip("@")

            try:
                monitored_id = db.get_monitoring_id(screen_name)
            except:
                await message.channel.send(strings.USER_NOT_IN_DB)
                return

            if duration == "24hrs":
                cursor = db.get_user_latest_by_time(int(time.time()) - 24*60*60, monitored_id)
            elif duration == "3d":
                cursor = db.get_user_latest_by_time(int(time.time()) - 3*24*60*60, monitored_id)
            elif duration == "7d":
                cursor = db.get_user_latest_by_time(int(time.time()) - 7*24*60*60, monitored_id)
            elif duration == "14d":
                cursor = db.get_user_latest_by_time(int(time.time()) - 14*24*60*60, monitored_id)
            elif duration == "30d":
                cursor = db.get_user_latest_by_time(int(time.time()) - 30*24*60*60, monitored_id)
            else:
                await message.channel.send(strings.INVALID_FORMAT)
                return

            monitored_id = ""
            for row in cursor:
                monitored_id = row[0]
                screen_name = row[1]
                following_id = row[2]

                await message.channel.send(f">>> https://twitter.com/{screen_name}")

            if monitored_id == "":
                await message.channel.send(strings.NO_NEW_FOLLOWING.format(duration))
                return

        except:
            try:
                duration = message.content.split()[1].strip("@")
                if duration == "24hrs":
                    cursor = db.get_latest_by_time(int(time.time()) - 24*60*60)
                elif duration == "3d":
                    cursor = db.get_latest_by_time(int(time.time()) - 3*24*60*60)
                elif duration == "7d":
                    cursor = db.get_latest_by_time(int(time.time()) - 7*24*60*60)
                elif duration == "14d":
                    cursor = db.get_latest_by_time(int(time.time()) - 14*24*60*60)
                elif duration == "30d":
                    cursor = db.get_latest_by_time(int(time.time()) - 30*24*60*60)
                else:
                    await message.channel.send(strings.INVALID_FORMAT)
                    return

                last_user = ""
                following_list = []
                compound_following_list = []
                print_list = []
                for row in cursor:
                    monitored_id = row[0]
                    screen_name = row[1]
                    following_id = row[2]

                    if last_user == monitored_id or last_user == "":
                        following_list.append(screen_name)
                    else:
                        compound_following_list.append(following_list)
                        print_list.append([db.get_screen_name(last_user), following_list])
                        following_list = []
                        following_list.append(screen_name)

                    last_user = monitored_id


                if last_user == "":
                    await message.channel.send(strings.NO_NEW_FOLLOWING.format(duration))
                    return

                compound_following_list.append(following_list)
                print_list.append([db.get_screen_name(last_user), following_list])

                print_list.sort(key=itemgetter(1), reverse=True)

                try:
                    result = set(compound_following_list[0])
                    for s in compound_following_list[1:]:
                        result.intersection_update(s)

                    common = ", ".join(list(result))
                except:
                    common = ""

                if common == "":
                    await message.channel.send(strings.NO_COMMON)
                else:
                    await message.channel.send(f">>> Common following(s) --> {common}")

                for ll in print_list:
                    try:
                        await message.channel.send(f">>> @{ll[0]} --> {len(ll[1])} new following \n{str(ll[1]).strip('[').strip(']')}")
                    except:
                        list_str = tweepy.de_join(str(ll[1]).strip('[').strip(']'))
                        await message.channel.send(f">>> @{ll[0]} --> {len(ll[1])} new following")
                        for string in list_str:
                            await message.channel.send(f">>> {string}")

            except:
                await message.channel.send(strings.WRONG_FORMAT)


async def user_metrics_background_task():
    await client.wait_until_ready()

    while True:
        guild = discord.utils.get(client.guilds, id=config.GUILD_ID)

        data = db.get_all_monitoring()
        for row in data:
            monitored_id = row[0]
            screen_name = row[1]
            print(f"getting followings for @{screen_name}")

            db.update_followings_id(monitored_id, "2")

            ids = await tweepy.get_following(monitored_id)

            monitor_count = db.count_monitor_by_id(monitored_id)

            for row in ids:
                db.insert_following(monitored_id, row[2], row[0], monitor_count)

            db.update_unfollowed_id(monitored_id, "0")

        data = db.get_all_pending()
        for row in data:
            screen_name = row[0]
            discord_id = int(row[1])

            try:
                id = await tweepy.get_id(screen_name)
                db.insert_monitoring(id, screen_name)
            except Exception as e:
                try:
                    db.delete_pending(screen_name)
                    member = await guild.fetch_member(discord_id)
                    await member.send(f">>> {member.mention}, user @{screen_name} can't be found on twitter")
                except:
                    pass

        for i in range(5 * 60):
            await asyncio.sleep(1)


client.loop.create_task(user_metrics_background_task())
client.run(config.DISCORD_TOKEN)

