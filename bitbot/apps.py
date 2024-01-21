from django.apps import AppConfig
import os, sys, threading, asyncio
import logging

logger = logging.getLogger(__name__)

class BitbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bitbot"
    
    def ready(self):
        if bool(int(os.environ.get("DISCORD_BOT_STARTED", "0"))):
            logger.info("[BitBot] Discord bot is already running")
        elif "runserver" in sys.argv:
            self.start_bot()
    
    def start_bot(self):
        logger.info("[BitBot] Starting the Discord bot")
        from . import bot
        
        threading.Thread(
            target=bot.main
        ).start()
        
        os.environ["DISCORD_BOT_STARTED"] = "1"
    
    def stop_bot(self, client):
        logger.info("[BitBot] Stopping the Discord bot")
        
        loop = asyncio.get_event_loop()
        loop.create_task(client.close())
        
        os.environ["DISCORD_BOT_STARTED"] = "0"
