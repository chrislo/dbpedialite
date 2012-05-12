require 'wikipedia_api'
require 'uri'

class BaseModel < Doodle
  has :pageid
  has :title, :default => nil
  has :displaytitle, :default => nil

  class << self
    has :identifier_path, :default => 'base'

    def load(pageid)
      object = self.new(pageid)
      object.load ? object : nil
    end
  end

  def initialize(pageid, args={})
    if pageid.kind_of?(Hash)
      args.merge!(pageid)
    else
      args.merge!(:pageid => pageid)
    end
    update(args)
    super(args)
  end

  # FIXME: can doodle be told to ignore unknown attributes?
  def update(args={})
    args.each_pair do |key,value|
      unless self.respond_to?(key)
        args.delete(key)
      end
    end
    doodle.update(args)
  end

  def uri
    @uri ||= RDF::URI.parse("http://dbpedialite.org/#{self.class.identifier_path}/#{pageid}#id")
  end

  def doc_uri=(uri)
    @doc_uri = RDF::URI.parse(uri.to_s)
  end

  def doc_uri
    @doc_uri || RDF::URI.parse("http://dbpedialite.org/#{self.class.identifier_path}/#{pageid}")
  end

  def doc_path(format=nil)
    "/#{self.class.identifier_path}/#{pageid}#{format ? '.' + format.to_s : ''}" 
  end

  def escaped_title
    unless title.nil?
      WikipediaApi.escape_title(title)
    end
  end

  def wikipedia_uri
    @wikipedia_uri ||= RDF::URI.parse("http://en.wikipedia.org/wiki/#{escaped_title}")
  end

  def dbpedia_uri
    @dbpedia_uri ||= RDF::URI.parse("http://dbpedia.org/resource/#{escaped_title}")
  end
end
