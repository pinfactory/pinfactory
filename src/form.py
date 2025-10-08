from flask_wtf import FlaskForm
from wtforms import (
    DecimalField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import AnyOf, ValidationError, DataRequired, NumberRange, URL


class OfferForm(FlaskForm):
    quantity = IntegerField(
        "quantity", validators=[DataRequired(), NumberRange(1, None)]
    )
    price = DecimalField(
        "price", places=3, validators=[DataRequired(), NumberRange(0.001, 0.999)]
    )
    side = SelectField(
        "side",
        choices=[("", "Select one"), ("FIXED", "FIXED"), ("UNFIXED", "UNFIXED")],
        validators=[AnyOf(["FIXED", "UNFIXED"])],
    )
    submit = SubmitField("Place offer")
    issue = HiddenField("issue")
    issuename = StringField("issuename", render_kw={"readonly": True})
    maturity = SelectField(
        "maturity", choices=[("", "Select one")], validators=[DataRequired()]
    )

    def __init__(self, maturities=None):
        super().__init__()
        mlist = [("", "Select a maturity date")]
        for m in maturities:
            mlist.append((m.id, m.display))
        self.maturity.choices = mlist


class ResolveForm(FlaskForm):
    contract_type = HiddenField("contract_type", validators=[NumberRange()])
    issue = HiddenField("issue", validators=[NumberRange()])
    maturity = HiddenField("maturity", validators=[NumberRange()])
    side = SelectField(
        "side",
        choices=[("", "Select one"), ("FIXED", "FIXED"), ("UNFIXED", "UNFIXED")],
        validators=[AnyOf(["FIXED", "UNFIXED"])],
    )
    submit = SubmitField("Resolve")


class OfferButton(FlaskForm):
    issue = HiddenField("issue")
    submit = SubmitField("Offers")


class IssueForm(FlaskForm):
    url = StringField(validators=[URL()])
    submit = SubmitField("Add issue")


class CancelButton(FlaskForm):
    offer = HiddenField("offer")
    submit = SubmitField("Cancel offer")


class MatchButton(FlaskForm):
    offer = HiddenField("offer")
    submit = SubmitField("Accept offer")


class OffsetForm(FlaskForm):
    position = HiddenField("position")
    submit = SubmitField("Trade")
