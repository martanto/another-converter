from masoniteorm.migrations import Migration

class CreateSeismicDataTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('seismic_data') as table:
            table.big_increments('id')
            table.string('filename')
            table.string('scnl')
            table.date('date')
            table.float('sampling_rate').default(0.0)
            table.float('max_amplitude').default(0.0)
            table.float('availability').default(0.0)
            table.big_integer('filesize').default(0)
            table.unique(['scnl','date'])
            table.index('date')
            table.index('scnl')
            table.timestamps().nullable()

    def down(self):
        self.schema.drop_if_exists('seismic_data')
