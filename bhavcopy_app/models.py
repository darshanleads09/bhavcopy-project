from django.db import models

class BhavCopy(models.Model):
    id = models.AutoField(primary_key=True)  # This will add an auto-increment primary key
    TradDt = models.DateField()  # Trade Date
    BizDt = models.DateField()  # Business Date
    Sgmt = models.CharField(max_length=10)  # Segment
    Src = models.CharField(max_length=10)  # Source
    FinInstrmTp = models.CharField(max_length=10)  # Financial Instrument Type
    FinInstrmId = models.IntegerField()  # Financial Instrument ID
    ISIN = models.CharField(max_length=12)  # ISIN
    TckrSymb = models.CharField(max_length=10)  # Ticker Symbol
    SctySrs = models.CharField(max_length=5, null=True, blank=True)  # Security Series
    XpryDt = models.DateField(null=True, blank=True)  # Expiry Date
    TtlTradgVol = models.IntegerField()  # Total Trading Volume
    TtlTrfVal = models.FloatField()  # Total Transfer Value
    TtlNbOfTxsExctd = models.IntegerField()  # Total Number of Transactions Executed
    SsnId = models.CharField(max_length=5)  # Session ID
    NewBrdLotQty = models.IntegerField()  # New Board Lot Quantity
    Rmks = models.CharField(max_length=255, null=True, blank=True)  # Remarks
    Rsvd1 = models.TextField(null=True, blank=True)  # Reserved Field 1
    Rsvd2 = models.TextField(null=True, blank=True)  # Reserved Field 2
    Rsvd3 = models.TextField(null=True, blank=True)  # Reserved Field 3
    Rsvd4 = models.TextField(null=True, blank=True)  # Reserved Field 4

    class Meta:
        db_table = 'BhavCopy'  # Use the existing 'BhavCopy' table
        managed = False  # Prevent Django from creating/modifying this table

    def __str__(self):
        return f"{self.TradDt} - {self.TckrSymb}"



# New Model for MCX BhavCopy Data
class BhavMCX(models.Model):
    id = models.AutoField(primary_key=True)  # This will add an auto-increment primary key
    date = models.DateField()
    symbol = models.CharField(max_length=50)
    expiry_date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    close_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    previous_close = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume = models.IntegerField(null=True, blank=True)
    volume_in_thousands = models.CharField(max_length=50, null=True, blank=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    open_interest = models.IntegerField(null=True, blank=True)
    date_display = models.CharField(max_length=50, null=True, blank=True)
    instrument_name = models.CharField(max_length=50, null=True, blank=True)
    strike_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    option_type = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bhav_mcx"

    def __str__(self):
        return f"{self.date} - {self.symbol} ({self.instrument_name})"
