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
        "price", places=3, validators=[DataRequired(), NumberRange(0, 1)]
    )
    side = SelectField(
        "side",
        choices=[("", "Select one"), ("FIXED", "FIXED"), ("UNFIXED", "UNFIXED")],
        validators=[AnyOf(["FIXED", "UNFIXED"])],
    )
    submit = SubmitField("Place offer")
    issue = HiddenField("issue")
    issuename = StringField("issuename", render_kw={"readonly": True})
    maturitydate = StringField("maturitydate", render_kw={"readonly": True})
    maturity = HiddenField("maturity")


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
    # FIXME: add label to show this is a 0-1 price
    price = DecimalField(
        "price",
        places=3,
        validators=[DataRequired("Enter a price between 0 and 1."), NumberRange(0, 1)],
    )
    submit = SubmitField("Sell contract")
