from mycroft import MycroftSkill, intent_file_handler, intent_handler
from mycroft.skills.core import resting_screen_handler
from adapt.intent import IntentBuilder
from mtranslate import translate
import feedparser
import random
from time import sleep
from os.path import join, dirname


class ChandraXRaySkill(MycroftSkill):
    def __init__(self):
        super(ChandraXRaySkill, self).__init__(name="ChandraXRaySkill")
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
                summary = translate(summary, self.lang)
                title = translate(title, self.lang)

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

    @resting_screen_handler("ChandraXRay - Latest")
    def idle(self, message):
        self.update_picture(not self.settings["random"])
        self.gui.clear()
        self.gui.show_page('idle.qml')

    # intents
    @intent_file_handler("about.intent")
    def handle_about_chandra_intent(self, message):
        epic = join(dirname(__file__), "ui", "images", "chandra.jpg")
        utterance = self.dialog_renderer.render("aboutChandra", {})
        self.gui.show_image(epic, override_idle=True,
                            fill='PreserveAspectFit', caption=utterance)
        self.speak(utterance, wait=True)
        sleep(1)
        self.gui.clear()

    @intent_file_handler('chandraxray.intent')
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

    @intent_handler(IntentBuilder("ExplainIntent")
                    .require("ExplainKeyword").require("ChandraXRay"))
    def handle_explain(self, message):
        self.gui.show_image(self.settings['imgLink'], override_idle=True,
                            fill='PreserveAspectFit',
                            caption=self.settings['summary'])
        self.speak(self.settings['summary'], wait=True)
        sleep(1)
        self.gui.clear()


def create_skill():
    return ChandraXRaySkill()