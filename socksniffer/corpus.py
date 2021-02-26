import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import pytz


class Corpus:
    def __init__(self, timezone=pytz.timezone('US/Pacific')):
        self.df = pd.DataFrame(columns=['entity', 'source', 'date', 'text'])
        self.timezone = timezone

    def load_data_from_csv(self, csv: str, kind: str = 'other', entity: str = None, source: str = None,
                           custom_mapping=None, sep=',', clean=True) -> None:

        twitter_mapping = {'created_at': 'date', 'comment': 'text'}

        if custom_mapping is None:
            custom_mapping = twitter_mapping

        if kind == 'twitter' or kind == 'gab':
            mapping = twitter_mapping

        else:
            mapping = custom_mapping

        try:
            data = pd.read_csv(csv, sep=sep)
            data.rename(mapping)
            data = data[['entity', 'source', 'date', 'text']]
            data['entity'] = entity
            data['source'] = source
            data['date'] = pd.to_datetime(data.date)
            fractional_hour = data.date.dt.minute / 60
            data['hour'] = pd.to_datetime(data.date).dt.tz_convert(self.timezone).dt.hour
            data['hour'] += fractional_hour
            data['hour_utc'] = pd.to_datetime(data.date).dt.tz_convert("UTC").dt.hour
            data['hour_utc'] += fractional_hour
            data['weekday'] = pd.to_datetime(data.date).dt.dayofweek

            if clean:
                # Filter out retweets
                data = data[~data.tweet.str.startswith('RT')]

                # Remove all @usernames
                data['tweet'] = data.tweet.str.replace('(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9-_]+)', '',
                                                       regex=True)

                # Remove all hashtags
                data['tweet'] = data.tweet.str.replace('(?:^|\s)[＃#]{1}(\w+)', '', regex=True)

                # Remove all t.co links
                data['tweet'] = data.tweet.str.replace('http[s]?:\/\/t\.co\/[0-9a-zA-Z]+', '', regex=True)

                # Remove multiple spaces
                data['tweet'] = data.tweet.str.replace('[\s]{2,10}', ' ', regex=True)

            self.df = pd.concat([self.df, data], axis=0)

        except KeyError as e:
            print(e)
            print('Ensure the data and chosen mapping match up.')

    def plot_activity(self, entity, hour='hour', subset_conditional=None, size=(7, 6), title=None, hue=None, cbar=True,
                      kind='hist', style=None, point_size=None, dodge=True, jitter=0.13):
        if subset_conditional:
            subset = self.df[subset_conditional]
        else:
            subset = self.df

        if title is None:
            title = entity + ' activity'

        if hour == 'hour_utc':
            tz = 'UTC'
        else:
            tz = self.timezone.zone

        plt.figure(figsize=size)

        if kind == 'hist':
            p = sns.histplot(data=subset, x='date', y=hour, bins=24, hue=hue, cbar=cbar).set_title(title)
        elif kind == 'scatter':
            p = sns.scatterplot(data=subset, x='date', y=hour, hue=hue, style=style, size=point_size).set_title(title)
        elif kind == 'week':
            sns.stripplot(data=subset, x='weekday', y=hour, size=point_size, hue=hue, jitter=jitter, dodge=dodge)
            plt.xticks(np.arange(7), ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'))

        else:
            Exception('Invalid "kind" chosen. Must be one of "hist", "scatter", or "week".')
            return

        plt.xticks(rotation=45)
        plt.yticks(np.arange(0, 25, step=4), ('Midnight', '4:00', '8:00', '12:00', '16:00', '20:00', 'Midnight'))
        plt.show()
        return p
