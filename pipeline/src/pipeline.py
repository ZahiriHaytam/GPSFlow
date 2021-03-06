import parser
import filters
import segment
import transport

def process(df) :
	days = getUniqueDays(df)
	result = []

	for day in days :
		raw_day = process_raw_day(day, df)
		segments, points = process_day(day, df)
		result.append({
				"date" : day,
				"segments" : segments,
				"points" : points,
				"raw_day" : raw_day
			})

	return result

def getUniqueDays(df) :
	sequence = df['date'].tolist()
	seen = set()
	return [x for x in sequence if not (x in seen or seen.add(x))]

def process_day(day, df) :
	min_angle=15
	max_speed=150
	median_window=2
	median_delay=150
	staypoint_limit=3
	staypoint_radius=50
	staypoint_outliers=5
	small_points=5
	small_distance=30

	# Select date
	df = parser.selectDate(day, df)

	# Apply filters
	df = filters.filterPerfectDuplicates(df)

	if df['date'].size > 5 :
		df = filters.filterByAngle(df, min_angle)
		df = filters.filterBySpeed(df, max_speed)
		df = filters.filterByMedian(df, n=median_window, min_delay=median_delay)

		# Segments by stay point
	if not df.empty :
		segments, points = segment.findSegments(df, staypoint_limit, staypoint_radius, staypoint_outliers)
		segments = segment.removeSmallSegments(segments, small_points, small_distance)
		points = segment.groupPoints(points)

		segments = transport.prepareDataKMeans(segments)
		segments = transport.fullSpeedSegmentation(segments)

		# Cleanup
		segments = cleanupColumns(segments)
		
		return segments, points
	else :
		return [], []

def cleanupColumns(segments) :
	for s in segments :
		s['ts'] = s['timestampMs']
		s['lat'] = s['latitude']
		s['lng'] = s['longitude']
		s['speed'] = s['speedClass']

	columns = ["ts", "lat", "lng", "speed", "numSC"]
	for s in segments :
		for col in list(s) :
			if col not in columns :
				del s[col]
				
	return segments

def process_raw_day(day, df) :
	raw_day = parser.selectDate(day, df)
	raw_day['lat'] = raw_day['latitude']
	raw_day['lng'] = raw_day['longitude']

	columns = ["lat", "lng"]
	for col in list(raw_day) :
		if col not in columns :
			del raw_day[col]
	
	return raw_day
