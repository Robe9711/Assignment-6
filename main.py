from aws_cdk import core
from corp_web import CorpWeb

app = core.App()

CorpWeb(app, "CorpWeb")
app.synth()
