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
