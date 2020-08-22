import asyncio
import json
import os

from collections import namedtuple
from queue import Queue

from aioquic.quic.configuration import QuicConfiguration

from adaptive.abr import BasicABR
from adaptive.mpc import MPC
from adaptive.bola import Bola
from adaptive.BBA0 import BBA0
from adaptive.BBA2 import BBA2

from clients.build import run

import config

adaptiveInfo = namedtuple("AdaptiveInfo",
                          'segment_time bitrates segments')
downloadInfo = namedtuple("DownloadInfo",
                          'index url quality resolution size downloaded time')


async def perform_download(configuration: QuicConfiguration, args) -> None:
	if args.urls is None:
		args.urls = config.URLS

	res = await run(
            configuration=configuration,
            urls=args.urls,
            data=args.data,
            include=args.include,
            legacy_quic=args.legacy_quic,
            output_dir=args.output_dir,
            local_port=args.local_port,
            zero_rtt=args.zero_rtt,
            session_ticket=args.session_ticket,
        )
	return res

def select_abr_algorithm(manifest_data, args):
	if args.abr == "BBA0":
		return BBA0(manifest_data)
	elif args.abr == 'Bola':
		return Bola(manifest_data)
	elif args.abr == 'tputRule':
		return BasicABR(manifest_data)
	elif args.abr == 'MPC':
		return MPC(manifest_data)
	elif args.abr == 'BBA2':
		return BBA2(manifest_data)
	else:
		print("Error!! No right rule specified")
		return


class DashClient:
	def __init__(self, configuration: QuicConfiguration, args):
		self.configuration = configuration
		self.args = args
		self.manifest_data = None
		self.latest_tput = 0
		self.totalBuffer = args.buffer_size
		self.currBuffer = 0
		self.abr_algorithm = None

		self.lastDownloadSize = 0

		self.segmentQueue = Queue(maxsize=0)
		self.frameQueue = Queue(maxsize=0)

		self.perf_parameters = {}
		self.perf_parameters['bitrate_change'] = []
		self.perf_parameters['prev_rate'] = 0
		self.perf_parameters['change_count'] = 0
		self.perf_parameters['rebuffer_time'] = 0.0
		self.perf_parameters['avg_bitrate'] = 0.0
		self.perf_parameters['avg_bitrate_change'] = 0.0
		self.perf_parameters['rebuffer_count'] = 0
		self.perf_parameters['tput_observed'] = []

	async def download_manifest(self) -> None:
		#TODO: Cleanup: globally intakes a list of urls, while here
		# we only consider a single urls per event.
		res = await perform_download(self.configuration, self.args)
		self.baseUrl, self.filename = os.path.split(self.args.urls[0])
		self.manifest_data = json.load(open(".cache/" + self.filename))
		self.lastDownloadSize = res[0][0]
		self.latest_tput = res[0][1]

	async def dash_client_set_config(self) -> None:
		await self.download_manifest()
		self.abr_algorithm = select_abr_algorithm(self.manifest_data, self.args)
		self.currentSegment = self.manifest_data['start_number'] - 1
		self.totalSegments = self.getTotalSegments()

	def getTotalSegments(self):
		return self.manifest_data['total_segments']

	def latest_segment_Throughput_kbps(self):
		# returns throughput value of last segment downloaded in kbps
		return self.latest_tput

	async def play(self) -> None:
		await self.dash_client_set_config()
		print(self.totalSegments)
		print(self.abr_algorithm)
		# print(self.manifest_data)
		# print(self.args.urls)
		# print(self.baseUrl)
		# print(self.filename)