from __future__ import annotations
import json, logging, time
logger = logging.getLogger(__name__)

class RuleEngine:
    def __init__(self, mqtt_client, config: dict):
        self.mqtt=mqtt_client; self.r=config.get("reminders",{})
        self._present: list[str]=[]; self._gtimes: dict[str,float]={}; self._dish: dict={}
        self._cd=float(config.get("face",{}).get("greeting_cooldown_minutes",60))*60

    def _speak(self,t): self.mqtt.publish("ha/tts/speak",json.dumps({"text":t}))
    def _fmt(self,k,fb,**kw):
        try: return self.r.get(k,fb).format(**kw)
        except KeyError: return self.r.get(k,fb)

    def on_face_detected(self,t,p):
        try: d=json.loads(p)
        except: return
        name=d.get("name","unknown"); conf=float(d.get("confidence",0))
        if name=="unknown" or conf<0.55: return
        now=time.monotonic()
        if now-self._gtimes.get(name,0)>self._cd:
            self._gtimes[name]=now
            self._speak(self._fmt("greeting_named","Hei {name}!",name=name))
            logger.info("Greeted %s",name)

    def on_presence_update(self,t,p):
        try: self._present=json.loads(p)
        except: self._present=[]

    def on_dish_alert(self,t,p):
        try: d=json.loads(p)
        except: return
        mins=int(d.get("minutes",0)); person=self._present[0] if self._present else None
        if person:
            self._speak(self._fmt("dishes_named",
                "Hei {name}, tiskipöydällä on ollut astioita jo {minutes} minuuttia.",
                name=person,minutes=mins))
        else:
            self._speak(self._fmt("dishes_unknown",
                "Tiskipöydällä on ollut astioita jo {minutes} minuuttia.",minutes=mins))

    def on_dish_status(self,t,p):
        try: self._dish=json.loads(p)
        except: pass

    def on_voice_command(self,t,p):
        try: text=json.loads(p).get("text","").lower().strip()
        except: return
        logger.info("Command: %s",text)
        if any(w in text for w in ["valot päälle","laita valot"]):
            self._speak(self.r.get("lights_on","Laitan valot päälle."))
            self.mqtt.publish("ha/light/control",json.dumps({"action":"on"}))
        elif any(w in text for w in ["sammuta valot","valot pois"]):
            self._speak(self.r.get("lights_off","Sammutin valot."))
            self.mqtt.publish("ha/light/control",json.dumps({"action":"off"}))
        elif any(w in text for w in ["tiskipöydällä","astioita","tiskit"]):
            if self._dish:
                self._speak(self._fmt("dishes_query_response","Näen: {items}.",items=", ".join(self._dish)))
            else:
                self._speak(self.r.get("dishes_empty","Tiskipöytä näyttää tyhjältä."))
        elif any(w in text for w in ["ketä","kuka","paikalla"]):
            if self._present:
                self._speak(self._fmt("present_response","Paikalla on: {names}.",names=", ".join(self._present)))
            else:
                self._speak(self.r.get("present_empty","Ketään ei näy."))
        else:
            self._speak(self.r.get("unknown_command","En ymmärtänyt komentoa."))
