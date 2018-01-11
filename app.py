# -*- coding: utf-8 -*-
import logging
import click
from pyassistant.app.assistant_base import AssistantBase
from pyassistant.asr.cognitive_speech import CognitiveSpeech
from pyassistant.record.sox_recorder import SoxRecorder
from pyassistant.slu.cognitive_luis import CognitiveLuis
from pyassistant.trigger.button_trigger import ButtonTrigger
from pyassistant.trigger.snowboy import Snowboy
from pyassistant.tts.open_jtalk import OpenJtalk

logging.basicConfig()
logger = logging.getLogger('pyassistant')
logger.setLevel(logging.INFO)

class PyAssistant(AssistantBase):
    def __init__(self):
        super().__init__()
        self.tts = OpenJtalk()

        if self.first_launch:
            self.setting = {
                'COGNITIVE_SPEECH_KEY': '',
                'COGNITIVE_LUIS_APPID': '',
                'COGNITIVE_LUIS_APPKEY': '',
                # snowboy or button
                'ACTIVATION_TRIGGER': 'snowboy',
                'RECORD_THRESHOLD': 4,
                'RECORD_BEGIN_SECOND': 0.1,
                'RECORD_END_SECOND': 1,
                'TRIGGER_GPIO': 21
            }

        if self.setting['COGNITIVE_SPEECH_KEY'] == '':
            raise Exception('COGNITIVE_SPEECH_KEY not found. please set ~/.pyassistant/setting.json')
        if self.setting['COGNITIVE_LUIS_APPID'] == '':
            raise Exception('COGNITIVE_LUIS_APPID not found. please set ~/.pyassistant/setting.json')
        if self.setting['COGNITIVE_LUIS_APPKEY'] == '':
            raise Exception('COGNITIVE_LUIS_APPKEY not found. please set ~/.pyassistant/setting.json')


    def conversation(self):

        yield ('CONVERSATION_START', None)

        while self.is_active:
            yield ('TURN_START', None)
            yield ('WAIT_TRIGGER', None)
            if self.setting['ACTIVATION_TRIGGER'] =='snowboy':
                trigger = Snowboy()
                is_detect = trigger.start(lambda :self.is_active,lambda :self.is_mute)
            elif self.setting['ACTIVATION_TRIGGER'] =='button':
                trigger = ButtonTrigger(int(self.setting['TRIGGER_GPIO']))
                is_detect = trigger.start(lambda :self.is_active)

            yield ('DETECT_TRIGGER',is_detect)
            if is_detect:
                self.play_sound_onoff(is_on=True)

                yield ('USER_SPEECH_START',None)
                recorder = SoxRecorder()
                recorder.threshold = self.setting['RECORD_THRESHOLD']
                recorder.start_second = self.setting['RECORD_BEGIN_SECOND']
                recorder.end_seond = self.setting['RECORD_END_SECOND']
                file = recorder.record()
                yield ('USER_SPEECH_END',file)
                self.play_sound_onoff(is_on=False)
                yield ('ASR_START',None)
                asr = CognitiveSpeech(self.setting['COGNITIVE_SPEECH_KEY'])
                asr_text = asr.recognize(file)
                yield ('ASR_FINISH', asr_text)

                if asr_text:
                    yield ('SLU_START', None)
                    slu = CognitiveLuis(
                        self.setting['COGNITIVE_LUIS_APPID'],
                        self.setting['COGNITIVE_LUIS_APPKEY']
                    )

                    intent,entities = slu.understand(asr_text)
                    yield ('SLU_FINISH',(intent,entities))
            else:
                raise Exception('Error in pyassistant')

            yield ('TURN_FINISH', None)

        yield ('CONVERSATION_FINISH', None)

    def say(self,text):
        self.tts.say(text)




@click.command()
@click.option('--debug','-d',default=0,type=int,help='enable debug mode if set 1')
def __main(debug):
    if debug >0:
        logger.setLevel(logging.DEBUG)

    with PyAssistant() as agent:
        while True:
            for event, content in agent.conversation():
                logger.info('------ [event] %s ------' % event)
                logger.info(content)



if __name__ == '__main__':
    __main()



