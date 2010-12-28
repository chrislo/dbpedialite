#!/usr/bin/ruby

require 'wikipedia_thing'


class DbpediaLite < Sinatra::Base
  set :public, File.dirname(__FILE__) + '/public'

  DEFAULT_HOST = 'dbpedialite.org'

  def self.extract_vocabularies(graph)
    vocabs = {}
    graph.predicates.each do |predicate|
      RDF::Vocabulary.each do |vocab|
        if predicate.to_s.index(vocab.to_uri.to_s) == 0
          vocab_name = vocab.__name__.split('::').last.downcase
          unless vocab_name.empty?
            vocabs[vocab_name.to_sym] = vocab
            break
          end
        end
      end
    end
    vocabs
  end
  
  def negotiate_content(graph, format, html_view)
    if format.empty?
      format = request.accept.first || ''
      format.sub!(/;.+$/,'')
    end

    headers 'Vary' => 'Accept',
            'Cache-Control' => 'public,max-age=600'
    case format
      when '', '*/*', 'html', 'application/xml', 'application/xhtml+xml', 'text/html' then
        content_type 'text/html'
        erb html_view
      when 'json', 'application/json', 'text/json' then
        content_type 'application/json'
        graph.dump(:json)
      when 'n3', 'ttl', 'text/n3', 'text/turtle', 'application/turtle' then
        content_type 'text/n3'
        graph.dump(:n3)
      when 'nt', 'ntriples', 'text/plain' then
        content_type 'text/plain'
        graph.dump(:ntriples)
      when 'rdf', 'xml', 'rdfxml', 'application/rdf+xml', 'text/rdf' then
        content_type 'application/rdf+xml'
        graph.dump(:rdfxml)
      else
        error 400, "Unsupported format: #{format}\n"
    end
  end

  helpers do
    include Rack::Utils
    include Sinatra::ContentFor
    alias_method :h, :escape_html

    def link_to(title, url=nil, attr={})
      url = title if url.nil?
      attr.merge!('href' => url.to_s)
      attr_str = attr.keys.map {|k| "#{h k}=\"#{h attr[k]}\""}.join(' ')
      "<a #{attr_str}>#{h title}</a>"
    end

    def nl2p(text)
      paragraphs = text.to_s.split(/[\n\r]+/)
      paragraphs.map {|para| "<p>#{para}</p>"}.join
    end

    def shorten(uri)
      qname = uri.qname.join(':') rescue uri.to_s
      escape_html(qname)
    end

    def format_xmlns(vocabularies)
      if vocabularies
        xmlns = ''
        vocabularies.each_pair do |prefix,vocab|
          xmlns += " xmlns:#{h prefix}=\"#{h vocab.to_uri}\""
        end
        xmlns
      end
    end

    def truncate(text, len=30, truncate_string='...')
      return if text.nil?
      l = len - truncate_string.chars.count
      text.chars.count > len ? text[/\A.{#{l}}\w*\;?/m][/.*[\w\;]/m] + truncate_string : text
    end

    def format_iso8061(datetime)
      datetime.strftime('%Y-%m-%dT%H:%M:%S%Z').sub(/\+00:00|UTC/, 'Z')
    end

  end

  before do
    if production? and request.host != DEFAULT_HOST
      headers 'Cache-Control' => 'public,max-age=3600'
      redirect "http://" + DEFAULT_HOST + request.path, 301
    end
  end

  get '/' do
    headers 'Cache-Control' => 'public,max-age=3600'
    @readme = RDiscount.new(File.read(File.join(File.dirname(__FILE__), 'README.md')))
    erb :index
  end

  get %r{^/search\.?([a-z]*)$} do |format|
    headers 'Cache-Control' => 'public,max-age=600'
    redirect '/' if params[:term].nil? or params[:term].empty?

    @results = WikipediaApi.search(params[:term], :srlimit => 20)
    @results.each do |result|
      escaped = CGI::escape(result['title'].gsub(' ','_'))
      result['url'] = "/titles/#{escaped}"
    end

    case format
      when '', 'html' then
        erb :search
      when 'json' then
        json = []
        @results.each do |r|
          json << {:label => r['title']}
        end
        content_type 'text/json'
        json.to_json
      else
        error 400, "Unsupported format: #{format}\n"
    end
  end

  get '/titles/:title' do |title|
    @thing = WikipediaThing.for_title(title)
    not_found("Title not found.") if @thing.nil?

    headers 'Cache-Control' => 'public,max-age=600'
    redirect "/things/#{@thing.pageid}", 301
  end

  get %r{^/things/(\d+)\.?([a-z0-9]*)$} do |pageid,format|
    @thing = WikipediaThing.load(pageid)
    not_found("Thing not found.") if @thing.nil?

    @thing.doc_uri = request.url
    @graph = @thing.to_rdf
    @vocabularies = DbpediaLite.extract_vocabularies(@graph)

    negotiate_content(@graph, format, :page)
  end

  get '/gems' do
    headers 'Cache-Control' => 'public,max-age=3600'
    @specs = Gem::loaded_specs.values.sort {|a,b| a.name <=> b.name }
    erb :gems
  end

end
