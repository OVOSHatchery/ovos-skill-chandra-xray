import random
from os.path import join, dirname
from time import sleep

import feedparser
from ovos_workshop.decorators import intent_handler
from ovos_workshop.decorators import resting_screen_handler
from ovos_workshop.intents import IntentBuilder
from ovos_workshop.skills import OVOSSkill


class ChandraXRaySkill(OVOSSkill):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "random" not in self.settings:
            # idle screen, random or latest
            self.settings["random"] = False

    def update_picture(self, latest=True):
        try:
            # TODO caching for 12h
            feed = "http://www.nasa.gov/rss/dyn/chandra_images.rss"
            e = feedparser.parse(feed)["entries"]
            if not latest:
                e = random.choice(e)
            else:
                e = e[0]
            summary = e["summary"]
            title = e["title"]
            imgLink = None
            if not self.lang.lower().startswith("en"):
                summary = self.translator.translate(summary, self.lang)
                title = self.translator.translate(title, self.lang)

            for link in e["links"]:
                if link["type"] == 'image/jpeg':
                    imgLink = \
                        "https://www.nasa.gov/sites/default/files/thumbnails" \
                        "/image/" + link["href"].split("/")[-1].split("?")[0]
            if imgLink:
                self.settings['imgLink'] = imgLink
                self.settings['title'] = title
                self.settings['summary'] = summary
                self.settings['url'] = e["id"]
        except Exception as e:
            self.log.exception(e)
        self.gui['imgLink'] = self.settings['imgLink']
        self.gui['title'] = self.settings['title']
        self.gui['summary'] = self.settings['summary']
        self.gui['url'] = self.settings['url']
        self.set_context("ChandraXRay")

    @resting_screen_handler("ChandraXRay")
    def idle(self, message):
        self.update_picture(not self.settings["random"])
        self.gui.clear()
        self.gui.show_page('idle.qml')

    # intents
    @intent_handler("about.intent")
    def handle_about_chandra_intent(self, message):
        picture = join(dirname(__file__), "ui", "images", "chandra.jpg")
        utterance = self.dialog_renderer.render("aboutChandra", {})
        self.gui.show_image(picture,
                            override_idle=True,
                            fill='PreserveAspectFit',
                            caption=utterance)
        self.speak(utterance, wait=True)
        sleep(1)
        self.gui.clear()

    @intent_handler('chandraxray.intent')
    def handle_pod(self, message):
        if self.voc_match(message.data["utterance"], "latest"):
            self.update_picture(True)
        else:
            self.update_picture(False)
        self.gui.clear()
        self.gui.show_image(self.settings['imgLink'],
                            caption=self.settings['title'],
                            fill='PreserveAspectFit')

        self.speak(self.settings['title'])

    @intent_handler(
        IntentBuilder("ExplainIntent").require("ExplainKeyword").require(
            "ChandraXRay"))
    def handle_explain(self, message):
        self.gui.show_image(self.settings['imgLink'],
                            override_idle=True,
                            fill='PreserveAspectFit',
                            caption=self.settings['summary'])
        self.speak(self.settings['summary'], wait=True)
        sleep(1)
        self.gui.clear()
