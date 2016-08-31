"""
The streams module defines the streams API that allows visualizations to
generate and respond to events, originating either in Python on the
server-side or in Javascript in the Jupyter notebook (client-side).
"""

import param
import uuid
from collections import OrderedDict



class Preprocessor(param.Parameterized):
    """
    A Preprocessor is a callable that takes a dictionary as an argument
    and returns a dictionary. Where possible, Preprocessors should have
    valid reprs that can be evaluated.

    Preprocessors are used to set the value of a stream based on the
    parameter values. They may be used for debugging purposes or to
    remap or repack parameter values before they are passed onto to the
    subscribers.
    """

    def __call__(self, params):
        return params



class Rename(Preprocessor):
    """
    A preprocesor used to rename parameter values.
    """

    def __init__(self, **mapping):
        self.mapping = mapping

    def __call__(self, params):
        return {self.mapping.get(k,k):v for (k,v) in params.items()}



class Stream(param.Parameterized):
    """
    A Stream is simply a parameterized object with parameters that
    change over time in response to update events. Parameters are
    updated via the update method.

    Streams may have one or more subscribers, callables that are passed
    the parameter dictionary when the trigger classmethod is called.
    """

    # Mapping from uuid to stream instance
    registry = OrderedDict()

    @classmethod
    def trigger(cls, streams):
        """
        Given a list of streams, collect all the stream parameters into
        a dictionary and pass it to the union set of subscribers.

        Passing multiple streams at once to trigger can be useful when a
        subscriber may be set multiple times across streams but only
        needs to be called once.
        """
        # Union of stream values
        items = [stream.value.items() for stream in streams]
        union = dict(kv for kvs in items for kv in kvs)
        # Currently building a simple set of subscribers
        groups = [stream.subscribers + stream._hidden_subscribers for stream in streams]
        subscribers = set(s for subscribers in groups for s in subscribers)
        for subscriber in subscribers:
            subscriber(union)

    def update(self, trigger=True, **kwargs):
        """
        The update method updates the stream parameters in response to
        some event.

        If trigger is enabled, the trigger classmethod is invoked on
        this particular Stream instance.
        """
        params = self.params().values()
        constants = [p.constant for p in params]
        for param in params:
            param.constant = False
        self.set_param(**kwargs)
        for (param, const) in zip(params, constants):
            param.constant = const

        if trigger:
            self.trigger([self])

    @classmethod
    def find(cls, obj):
        """
        Return a set of streams from the registry with a given source.
        """
        return set(v for v in cls.registry.values() if v.source is obj)

    def __init__(self, mapping=None, source=None,
                 subscribers=[], preprocessors=[], **params):
        """
        Mapping allows multiple streams with similar event state to be
        used by remapping parameter names.

        Source is an optional argument specifying the HoloViews
        datastructure that the stream receives events from, as supported
        by the plotting backend.
        """
        self.source = source
        self.subscribers = subscribers
        self.preprocessors = preprocessors
        self._hidden_subscribers = []

        if mapping is None:
            self.mapping = {}
        elif isinstance(mapping, dict):
            # Could do some validation here
            self.mapping = mapping
        elif len(self.params()) == 2:
            self.mapping = {k:mapping for k in self.params() if k != 'name'}
        else:
            raise Exception("Stream has multiple parameters, please supply a dictionary")

        self.uuid = uuid.uuid4().hex
        super(Stream, self).__init__(**params)
        self.registry[self.uuid] = self

    @property
    def value(self):
        remapped =  {self.mapping.get(k,k):v for (k,v) in self.get_param_values()
                     if k != 'name'}
        for preprocessor in self.preprocessors:
            remapped = preprocessor(remapped)
        return remapped

    def __repr__(self):
        cls_name = self.__class__.__name__
        kwargs = ','.join('%s=%r' % (k,v)
                          for (k,v) in self.get_param_values() if k != 'name')
        if not self.mapping:
            return '%s(%s)' % (cls_name, kwargs)
        elif len(self.mapping) == 1:
            return '%s(%r, %s)' % (cls_name, self.mapping.values()[0], kwargs)
        else:
            return '%s(%r, %s)' % (cls_name, self.mapping, kwargs)

    def __str__(self):
        return repr(self)


class PositionX(Stream):
    """
    A position along the x-axis in data coordinates.

    With the appropriate plotting backend, this may correspond to the
    position of the mouse/trackpad cursor.
    """

    x = param.Number(default=0, doc="""
           Position along the x-axis in data coordinates""", constant=True)

    def __init__(self, mapping=None, **params):
        super(PositionX, self).__init__(mapping=mapping, **params)


class PositionY(Stream):
    """
    A position along the y-axis in data coordinates.

    With the appropriate plotting backend, this may correspond to the
    position of the mouse/trackpad cursor.
    """

    y = param.Number(default=0, doc="""
           Position along the y-axis in data coordinates""", constant=True)

    def __init__(self, mapping=None, **params):
        super(PositionY, self).__init__(mapping=mapping, **params)


class PositionXY(Stream):
    """
    A position along the x- and y-axes in data coordinates.

    With the appropriate plotting backend, this may correspond to the
    position of the mouse/trackpad cursor.
    """


    x = param.Number(default=0, doc="""
           Position along the x-axis in data coordinates""", constant=True)

    y = param.Number(default=0, doc="""
           Position along the y-axis in data coordinates""", constant=True)

    def __init__(self, mapping=None, **params):
        super(PositionXY, self).__init__(mapping=mapping, **params)
